package main

import (
	"bytes"
	"compress/zlib"
	"context"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

func TestClientNearestRankAndDrain(t *testing.T) {
	got := nearestRank([]int64{9, 1, 7, 3}, .5)
	if got != 3 {
		t.Fatalf("p50 %d want3", got)
	}
	if nearestRank([]int64{1, 2, 3}, .99) != 3 || nearestRank(nil, .95) != 0 {
		t.Fatal("quantile boundary")
	}
	if d := measurementDrain(10*time.Millisecond, 15*time.Millisecond); d != 5*time.Millisecond {
		t.Fatalf("drain %v", d)
	}
	if d := measurementDrain(10*time.Millisecond, 8*time.Millisecond); d != 0 {
		t.Fatalf("negative drain %v", d)
	}
}

func TestClientFixedWindowCountsIncludeDeadlineBoundary(t *testing.T) {
	rows := []ClientRecord{{Success: true, Completion: true, EndOffsetNS: 90, LatencyNS: 1}, {Success: true, Completion: true, EndOffsetNS: 100, LatencyNS: 1}, {Success: true, Completion: true, EndOffsetNS: 101, LatencyNS: 1}, {Error: "timeout", ErrorClass: "transport", Completion: true, EndOffsetNS: 110, LatencyNS: 1}}
	raw, _ := json.Marshal(summarizeClient(rows, 100, 120))
	var m map[string]any
	json.Unmarshal(raw, &m)
	if m["fixed_window_verified_success"] != float64(2) || m["fixed_window_throughput_success_per_sec"] != float64(20_000_000) || m["drain_completions"] != float64(2) {
		t.Fatalf("fixed window counters %s", raw)
	}
}

func TestClientRejectsFrameOracleMismatchAfterNativeVerification(t *testing.T) {
	a, id := fixtureArchive(t)
	s, e := NewService(a, 1, false)
	if e != nil {
		t.Fatal(e)
	}
	a.cases[id].references[0]["ordinary"] = []byte("wrong-archived-oracle")
	ts := httptest.NewServer(s.Handler())
	defer ts.Close()
	c := ClientConfig{URL: ts.URL, CaseID: id, Mode: "ordinary", Timeout: time.Second}
	bodies, _ := clientBodies(c, a)
	cl, tr := newWorkerClient(time.Second)
	defer tr.CloseIdleConnections()
	row := performClientRequest(context.Background(), cl, c, a, 0, 0, 0, bodies[0], time.Now())
	if row.Success || row.ErrorClass != "integrity" || !strings.Contains(row.Error, "differs from archived codec frame") {
		t.Fatalf("frame oracle gate failed %+v", row)
	}
}

func TestClientRejectsValidAlternateZlibBytes(t *testing.T) {
	a, id := fixtureArchive(t)
	worker, _ := a.NewWorker()
	ordinary, _, _ := worker.Serve(id, 0, "ordinary")
	var compressed bytes.Buffer
	zw, _ := zlib.NewWriterLevel(&compressed, zlib.NoCompression)
	zw.Write(ordinary[4:])
	zw.Close()
	alternate := append([]byte{'E', '3', 2, 0}, compressed.Bytes()...)
	restored, e := decodeStudy(alternate, "zlib-ordinary")
	if e != nil || !a.Accept(id, 0, restored) || a.FrameMatches(id, 0, "zlib-ordinary", alternate) {
		t.Fatal("alternate zlib fixture not valid or not distinct")
	}
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("X-R8-Replay", "false")
		w.Header().Set("X-R8-Queue-Ns", "0")
		w.Header().Set("X-R8-Proof-Ns", "0")
		w.Header().Set("X-R8-Encode-Ns", "0")
		w.Header().Set("Content-Length", strconv.Itoa(len(alternate)))
		w.Write(alternate)
	}))
	defer ts.Close()
	c := ClientConfig{URL: ts.URL, CaseID: id, Mode: "zlib-ordinary", Timeout: time.Second}
	bodies, _ := clientBodies(c, a)
	cl, tr := newWorkerClient(time.Second)
	defer tr.CloseIdleConnections()
	row := performClientRequest(context.Background(), cl, c, a, 0, 0, 0, bodies[0], time.Now())
	if row.Success || row.ErrorClass != "integrity" || !strings.Contains(row.Error, "differs from archived codec frame") {
		t.Fatalf("alternate valid codec frame accepted: %+v", row)
	}
}

func TestClientEarlyBodyCloseIsTransportFailure(t *testing.T) {
	a, id := fixtureArchive(t)
	worker, _ := a.NewWorker()
	good, _, _ := worker.Serve(id, 0, "ordinary")
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Length", strconv.Itoa(len(good)+1))
		w.Header().Set("X-R8-Replay", "false")
		w.Header().Set("X-R8-Queue-Ns", "0")
		w.Header().Set("X-R8-Proof-Ns", "0")
		w.Header().Set("X-R8-Encode-Ns", "0")
		w.Write(good)
	}))
	defer ts.Close()
	c := ClientConfig{URL: ts.URL, CaseID: id, Mode: "ordinary", Timeout: time.Second}
	bodies, _ := clientBodies(c, a)
	cl, tr := newWorkerClient(time.Second)
	defer tr.CloseIdleConnections()
	row := performClientRequest(context.Background(), cl, c, a, 0, 0, 0, bodies[0], time.Now())
	if row.Success || row.ErrorClass != "transport" || row.BodyBytes != len(good) {
		t.Fatalf("incomplete HTTP body classified incorrectly: %+v", row)
	}
}

func TestClientServerReplayMismatchInvalidatesReceipt(t *testing.T) {
	a, id := fixtureArchive(t)
	s, e := NewService(a, 1, false)
	if e != nil {
		t.Fatal(e)
	}
	var snapshots atomic.Int64
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/stats" {
			json.NewEncoder(w).Encode(map[string]bool{"replay": snapshots.Add(1) > 1})
			return
		}
		s.Handler().ServeHTTP(w, r)
	}))
	defer ts.Close()
	dir := t.TempDir()
	c := ClientConfig{URL: ts.URL, CaseID: id, Mode: "ordinary", Concurrency: 1, Duration: time.Millisecond, Timeout: time.Second, WorkDir: dir}
	if e = RunClient(c, a); e == nil {
		t.Fatal("server replay change accepted")
	}
	raw, e := os.ReadFile(filepath.Join(dir, "summary.json"))
	var summary ClientSummary
	if e != nil || json.Unmarshal(raw, &summary) != nil || summary.MeasurementComplete || summary.IntegrityOK || summary.StopReason != "server_replay_mismatch" {
		t.Fatalf("invalid replay receipt %s %v", raw, e)
	}
}

func TestClientRejectsMalformedTruncatedAndWrongBinding(t *testing.T) {
	a, id := fixtureArchive(t)
	w, _ := a.NewWorker()
	good, _, _ := w.Serve(id, 0, "ordinary")
	b, _ := decodeStudy(good, "ordinary")
	b.Root[0] ^= 1
	wrong, _ := NewEncoder().Encode(b, "ordinary")
	for _, tc := range []struct {
		name   string
		body   []byte
		delay  time.Duration
		status int
	}{{"malformed", []byte("bad"), 0, 200}, {"truncated", good[:len(good)-1], 0, 200}, {"wrong-root", wrong, 0, 200}, {"timeout", good, 60 * time.Millisecond, 200}, {"error-status", []byte("failure"), 0, 503}} {
		t.Run(tc.name, func(t *testing.T) {
			ts := httptest.NewServer(http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
				time.Sleep(tc.delay)
				rw.Header().Set("X-R8-Replay", "false")
				rw.Header().Set("X-R8-Queue-Ns", "1")
				rw.Header().Set("X-R8-Proof-Ns", "2")
				rw.Header().Set("X-R8-Encode-Ns", "3")
				rw.WriteHeader(tc.status)
				rw.Write(tc.body)
			}))
			defer ts.Close()
			c := ClientConfig{URL: ts.URL, CaseID: id, Mode: "ordinary", Timeout: 20 * time.Millisecond}
			bodies, e := clientBodies(c, a)
			if e != nil {
				t.Fatal(e)
			}
			cl, tr := newWorkerClient(c.Timeout)
			defer tr.CloseIdleConnections()
			row := performClientRequest(context.Background(), cl, c, a, 0, 0, 0, bodies[0], time.Now())
			if row.Error == "" || row.Success {
				t.Fatalf("invalid response counted: %+v", row)
			}
			wantClass := "integrity"
			if tc.name == "timeout" {
				wantClass = "transport"
			}
			if tc.name == "error-status" {
				wantClass = "http"
			}
			if row.ErrorClass != wantClass {
				t.Fatalf("error class %q want %q: %+v", row.ErrorClass, wantClass, row)
			}
		})
	}
}

func TestClientIntegrityFailureStopsAdmissionAndRetainsInvalidReceipt(t *testing.T) {
	a, id := fixtureArchive(t)
	s, e := NewService(a, 1, false)
	if e != nil {
		t.Fatal(e)
	}
	var reads atomic.Int64
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/read" && reads.Add(1) == 2 {
			w.Header().Set("X-R8-Queue-Ns", "1")
			w.Header().Set("X-R8-Proof-Ns", "2")
			w.Header().Set("X-R8-Encode-Ns", "3")
			w.Write([]byte("bad-frame"))
			return
		}
		s.Handler().ServeHTTP(w, r)
	}))
	defer ts.Close()
	dir := t.TempDir()
	c := ClientConfig{URL: ts.URL, CaseID: id, Mode: "ordinary", Concurrency: 1, Warmup: 0, Duration: 500 * time.Millisecond, Timeout: time.Second, WorkDir: dir}
	if e = RunClient(c, a); e == nil {
		t.Fatal("integrity failure accepted")
	}
	var summary ClientSummary
	raw, e := os.ReadFile(filepath.Join(dir, "summary.json"))
	if e != nil || json.Unmarshal(raw, &summary) != nil {
		t.Fatal("missing invalid summary", e)
	}
	if summary.Attempted != 1 || summary.Errors != 1 || summary.MeasurementComplete || summary.IntegrityOK || summary.StopReason != "integrity_failure" || summary.AdmissionNS >= summary.NominalNS {
		t.Fatalf("invalid abort receipt: %+v", summary)
	}
	var receipt struct {
		Complete          bool `json:"complete"`
		RecordingComplete bool `json:"recording_complete"`
	}
	raw, e = os.ReadFile(filepath.Join(dir, "completion.json"))
	if e != nil || json.Unmarshal(raw, &receipt) != nil || receipt.Complete || !receipt.RecordingComplete {
		t.Fatal("missing incomplete completion receipt", e)
	}
}

func TestClientWarmupFailureStopsOtherLoops(t *testing.T) {
	a, id := fixtureArchive(t)
	s, e := NewService(a, 2, false)
	if e != nil {
		t.Fatal(e)
	}
	var reads atomic.Int64
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/read" && reads.Add(1) == 1 {
			w.Header().Set("X-R8-Queue-Ns", "1")
			w.Header().Set("X-R8-Proof-Ns", "2")
			w.Header().Set("X-R8-Encode-Ns", "3")
			w.Write([]byte("bad-frame"))
			return
		}
		// Keep the other stream in flight while the immediate bad frame is
		// classified. Counting arbitrarily fast replies here makes this stop
		// assertion depend on relative goroutine scheduling under -race.
		if r.URL.Path == "/read" {
			time.Sleep(10 * time.Millisecond)
		}
		s.Handler().ServeHTTP(w, r)
	}))
	defer ts.Close()
	dir := t.TempDir()
	c := ClientConfig{URL: ts.URL, CaseID: id, Mode: "ordinary", Concurrency: 2, Warmup: 200 * time.Millisecond, Duration: time.Millisecond, Timeout: time.Second, WorkDir: dir}
	if e = RunClient(c, a); e == nil {
		t.Fatal("invalid warmup accepted")
	}
	if got := reads.Load(); got > 4 {
		t.Fatalf("warmup kept admitting after integrity failure: %d requests", got)
	}
	var report struct {
		Counts ClientCounts `json:"counts"`
	}
	raw, e := os.ReadFile(filepath.Join(dir, "warmup.json"))
	if e != nil || json.Unmarshal(raw, &report) != nil || report.Counts.Errors < 1 {
		t.Fatal("warmup failure not retained", e)
	}
	var receipt struct {
		Complete          bool   `json:"complete"`
		RecordingComplete bool   `json:"recording_complete"`
		StopReason        string `json:"stop_reason"`
	}
	raw, e = os.ReadFile(filepath.Join(dir, "completion.json"))
	if e != nil || json.Unmarshal(raw, &receipt) != nil || receipt.Complete || !receipt.RecordingComplete || receipt.StopReason != "warmup_failure" {
		t.Fatal("failed warmup receipt missing or misleading", e)
	}
}

func TestClientOrderedRequestAndPersistentConnection(t *testing.T) {
	a, id := fixtureArchive(t)
	s, e := NewService(a, 2, false)
	if e != nil {
		t.Fatal(e)
	}
	var conns atomic.Int64
	ts := httptest.NewUnstartedServer(s.Handler())
	ts.Config.ConnState = func(_ net.Conn, st http.ConnState) {
		if st == http.StateNew {
			conns.Add(1)
		}
	}
	ts.Start()
	defer ts.Close()
	c := ClientConfig{URL: ts.URL, CaseID: id, Mode: "dictionary", Timeout: time.Second}
	bodies, e := clientBodies(c, a)
	if e != nil {
		t.Fatal(e)
	}
	var req struct {
		CaseID string   `json:"case_id"`
		Batch  int      `json:"batch"`
		Mode   string   `json:"mode"`
		Keys   [][]byte `json:"keys"`
	}
	if e = json.Unmarshal(bodies[0], &req); e != nil {
		t.Fatal(e)
	}
	keys, _ := a.RequestKeys(id, 0)
	if len(req.Keys) != 3 || !bytes.Equal(req.Keys[0], req.Keys[1]) || !bytes.Equal(req.Keys[2], keys[2]) {
		t.Fatal("request lost ordered duplicate keys")
	}
	cl, tr := newWorkerClient(time.Second)
	defer tr.CloseIdleConnections()
	for i := 0; i < 6; i++ {
		row := performClientRequest(context.Background(), cl, c, a, 0, int64(i), i%3, bodies[i%3], time.Now())
		if !row.Success || row.Error != "" || row.RequestBodyBytes != len(bodies[i%3]) {
			t.Fatalf("roundtrip %+v", row)
		}
	}
	if conns.Load() != 1 {
		t.Fatalf("connections %d want1", conns.Load())
	}
}

func TestRunClientRetainsRowsAndCompletion(t *testing.T) {
	a, id := fixtureArchive(t)
	s, e := NewService(a, 2, false)
	if e != nil {
		t.Fatal(e)
	}
	ts := httptest.NewServer(s.Handler())
	defer ts.Close()
	dir := t.TempDir()
	c := ClientConfig{URL: ts.URL, CaseID: id, Mode: "ordinary", Concurrency: 2, Warmup: time.Millisecond, Duration: 15 * time.Millisecond, Timeout: time.Second, WorkDir: dir}
	if e = RunClient(c, a); e != nil {
		t.Fatal(e)
	}
	var summary ClientSummary
	b, e := os.ReadFile(filepath.Join(dir, "summary.json"))
	if e != nil || json.Unmarshal(b, &summary) != nil {
		t.Fatal("missing summary", e)
	}
	log, e := os.ReadFile(filepath.Join(dir, "log.jsonl"))
	if e != nil {
		t.Fatal(e)
	}
	if n := int64(bytes.Count(log, []byte("\n"))); n != summary.Attempted || n != summary.Success || summary.Errors != 0 || !summary.IntegrityOK {
		t.Fatalf("rows=%d summary=%+v", n, summary)
	}
	for _, line := range bytes.Split(bytes.TrimSpace(log), []byte("\n")) {
		var row ClientRecord
		if json.Unmarshal(line, &row) != nil || row.Batch != (row.Worker+int(row.Seq))%3 || row.BodyCompleteOffsetNS > row.EndOffsetNS || row.BodyReadNS < 0 {
			t.Fatalf("unbalanced worker batch %s", line)
		}
	}
	if summary.DurationNS < summary.NominalNS || summary.DrainNS != summary.DurationNS-summary.NominalNS || summary.LatencyNS.P99 <= 0 || summary.Warmup.Success < 2 {
		t.Fatalf("invalid duration/warmup %+v", summary)
	}
	for _, name := range []string{"completion.json", "config.json", "environment.json"} {
		if _, e = os.Stat(filepath.Join(dir, name)); e != nil {
			t.Fatal(name, e)
		}
	}
	if summary.ThroughputSuccessPerSec != float64(summary.Success)/(float64(summary.DurationNS)/float64(time.Second)) {
		t.Fatal(fmt.Sprint("incorrect denominator ", summary))
	}
}
