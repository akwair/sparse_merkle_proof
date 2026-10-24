package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

// Each client loop owns its transport, request sequence, response and row buffer.
// No output is written during either the warmup or measurement loops.
type ClientConfig struct {
	Data        string        `json:"data"`
	URL         string        `json:"url"`
	CaseID      string        `json:"case_id"`
	Mode        string        `json:"mode"`
	WorkDir     string        `json:"work_dir"`
	Concurrency int           `json:"concurrency"`
	Warmup      time.Duration `json:"warmup_ns"`
	Duration    time.Duration `json:"duration_ns"`
	Timeout     time.Duration `json:"timeout_ns"`
}

type ClientRecord struct {
	Worker               int                 `json:"worker"`
	Seq                  int64               `json:"seq"`
	Batch                int                 `json:"batch"`
	Mode                 string              `json:"mode"`
	CaseID               string              `json:"case_id"`
	StartOffsetNS        int64               `json:"start_offset_ns"`
	EndOffsetNS          int64               `json:"end_offset_ns"`
	LatencyNS            int64               `json:"latency_ns"`
	DecodeVerifyNS       int64               `json:"decode_verify_ns"`
	BodyReadNS           int64               `json:"body_read_ns"`
	BodyCompleteOffsetNS int64               `json:"body_complete_offset_ns"`
	ServerQueueNS        int64               `json:"server_queue_ns"`
	ServerProofNS        int64               `json:"server_proof_ns"`
	ServerEncodeNS       int64               `json:"server_encode_ns"`
	BodyBytes            int                 `json:"body_bytes"`
	RequestBodyBytes     int                 `json:"request_body_bytes"`
	Error                string              `json:"error"`
	ErrorClass           string              `json:"error_class"`
	Completion           bool                `json:"completion"`
	Success              bool                `json:"success"`
	ServerHeaders        map[string][]string `json:"server_headers"`
	Replay               bool                `json:"replay"`
}

type ClientCounts struct {
	Attempted int64 `json:"attempted"`
	Success   int64 `json:"success"`
	Errors    int64 `json:"errors"`
}

type ClientQuantiles struct {
	P50 int64 `json:"p50"`
	P95 int64 `json:"p95"`
	P99 int64 `json:"p99"`
	Max int64 `json:"max"`
}

type ClientRawSums struct {
	LatencyNS      int64 `json:"latency_ns"`
	DecodeVerifyNS int64 `json:"decode_verify_ns"`
	ServerQueueNS  int64 `json:"server_queue_ns"`
	ServerProofNS  int64 `json:"server_proof_ns"`
	ServerEncodeNS int64 `json:"server_encode_ns"`
}

type ClientBytes struct {
	ResponseBodySum int64 `json:"response_body_bytes_sum"`
	RequestBodySum  int64 `json:"request_body_bytes_sum"`
	ResponseBodyMin int   `json:"response_body_bytes_min"`
	ResponseBodyMax int   `json:"response_body_bytes_max"`
}

type ClientMemorySnapshot struct {
	HeapAlloc    uint64 `json:"heap_alloc"`
	HeapSys      uint64 `json:"heap_sys"`
	TotalAlloc   uint64 `json:"total_alloc"`
	NumGC        uint32 `json:"num_gc"`
	PauseTotalNS uint64 `json:"pause_total_ns"`
}

type ClientSummary struct {
	Schema                             string               `json:"schema"`
	Attempted                          int64                `json:"attempted"`
	Success                            int64                `json:"success"`
	Errors                             int64                `json:"errors"`
	NominalNS                          int64                `json:"nominal_ns"`
	DurationNS                         int64                `json:"duration_ns"`
	DrainNS                            int64                `json:"drain_ns"`
	AdmissionNS                        int64                `json:"admission_ns"`
	StopReason                         string               `json:"stop_reason"`
	ThroughputSuccessPerSec            float64              `json:"throughput_success_per_sec"`
	NominalSuccessPerSec               float64              `json:"nominal_success_per_sec"`
	AdmissionSuccessPerSec             float64              `json:"admission_success_per_sec"`
	ErrorCounts                        map[string]int64     `json:"error_counts"`
	FixedWindowVerifiedSuccess         int64                `json:"fixed_window_verified_success"`
	FixedWindowThroughputSuccessPerSec float64              `json:"fixed_window_throughput_success_per_sec"`
	DrainCompletions                   int64                `json:"drain_completions"`
	ServerReplay                       bool                 `json:"server_replay"`
	PrimaryThroughputMetric            string               `json:"primary_throughput_metric"`
	LatencyNS                          ClientQuantiles      `json:"latency_ns"`
	RawSums                            ClientRawSums        `json:"raw_sums"`
	Bytes                              ClientBytes          `json:"bytes"`
	Warmup                             ClientCounts         `json:"warmup"`
	ClientMemBefore                    ClientMemorySnapshot `json:"client_mem_before"`
	ClientMemAfter                     ClientMemorySnapshot `json:"client_mem_after"`
	ClientProcBefore                   map[string]string    `json:"client_proc_before"`
	ClientProcAfter                    map[string]string    `json:"client_proc_after"`
	ServerStatsBefore                  json.RawMessage      `json:"server_stats_before"`
	ServerStatsAfter                   json.RawMessage      `json:"server_stats_after"`
	IntegrityOK                        bool                 `json:"integrity_ok"`
	MeasurementComplete                bool                 `json:"measurement_complete"`
	LatencyMeaning                     string               `json:"latency_meaning"`
	LatencyMetric                      string               `json:"latency_metric"`
	ThroughputMeaning                  string               `json:"throughput_meaning"`
	QuantileMethod                     string               `json:"quantile_method"`
	AdmissionStartUTC                  string               `json:"admission_start_utc"`
	MeasurementEndUTC                  string               `json:"measurement_end_utc"`
}

func clientMemorySnapshot() ClientMemorySnapshot {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	return ClientMemorySnapshot{m.HeapAlloc, m.HeapSys, m.TotalAlloc, m.NumGC, m.PauseTotalNs}
}

func (c ClientConfig) validate() error {
	u, e := url.Parse(c.URL)
	if e != nil || u.Scheme != "http" || u.Host == "" || u.User != nil || u.RawQuery != "" || u.Fragment != "" || (u.Path != "" && u.Path != "/") {
		return fmt.Errorf("url must be an HTTP origin")
	}
	if c.Concurrency < 1 || c.Concurrency > 4096 || c.Warmup < 0 || c.Duration <= 0 || c.Timeout <= 0 {
		return fmt.Errorf("invalid concurrency or client duration")
	}
	if !validMode(c.Mode) || c.CaseID == "" {
		return fmt.Errorf("invalid mode or case")
	}
	return nil
}

func clientBodies(c ClientConfig, a *Archive) ([3][]byte, error) {
	var out [3][]byte
	for batch := range out {
		keys, e := a.RequestKeys(c.CaseID, batch)
		if e != nil {
			return out, e
		}
		body := struct {
			CaseID string   `json:"case_id"`
			Batch  int      `json:"batch"`
			Mode   string   `json:"mode"`
			Keys   [][]byte `json:"keys"`
		}{c.CaseID, batch, c.Mode, keys}
		out[batch], e = json.Marshal(body)
		if e != nil {
			return out, e
		}
	}
	return out, nil
}

func newWorkerClient(timeout time.Duration) (*http.Client, *http.Transport) {
	tr := &http.Transport{Proxy: nil, DisableCompression: true, ForceAttemptHTTP2: false, MaxConnsPerHost: 1, MaxIdleConns: 1, MaxIdleConnsPerHost: 1, IdleConnTimeout: 90 * time.Second, ResponseHeaderTimeout: timeout}
	cl := &http.Client{Transport: tr, Timeout: timeout, CheckRedirect: func(_ *http.Request, _ []*http.Request) error { return http.ErrUseLastResponse }}
	return cl, tr
}

func performClientRequest(ctx context.Context, cl *http.Client, c ClientConfig, a *Archive, worker int, seq int64, batch int, body []byte, epoch time.Time) ClientRecord {
	return performClientRequestAt(ctx, cl, c, a, worker, seq, batch, body, epoch, time.Now())
}

func performClientRequestAt(ctx context.Context, cl *http.Client, c ClientConfig, a *Archive, worker int, seq int64, batch int, body []byte, epoch, admitted time.Time) (row ClientRecord) {
	row = ClientRecord{Worker: worker, Seq: seq, Batch: batch, Mode: c.Mode, CaseID: c.CaseID, StartOffsetNS: admitted.Sub(epoch).Nanoseconds(), RequestBodyBytes: len(body)}
	var responseRaw []byte
	var restored Bundle
	defer func() {
		end := time.Now()
		row.EndOffsetNS = end.Sub(epoch).Nanoseconds()
		row.LatencyNS = end.Sub(admitted).Nanoseconds()
		// The archive byte oracle is a preservation gate after the latency endpoint.
		// Its work remains in the closed-loop schedule and actual elapsed denominator.
		if row.Error == "" && !a.FrameMatches(c.CaseID, batch, c.Mode, responseRaw) {
			row.Error = "response differs from archived codec frame"
			row.ErrorClass = "integrity"
		}
		runtime.KeepAlive(responseRaw)
		runtime.KeepAlive(restored)
		row.Completion = true
		row.Success = row.Error == ""
		if row.Error != "" && row.ErrorClass == "" {
			row.ErrorClass = "integrity"
		}
	}()
	// Suppressing GetBody makes this non-idempotent POST non-replayable by Transport.
	req, e := http.NewRequestWithContext(ctx, http.MethodPost, strings.TrimRight(c.URL, "/")+"/read", bytes.NewReader(body))
	if e != nil {
		row.Error = e.Error()
		row.ErrorClass = "transport"
		return
	}
	req.GetBody = nil
	req.Header.Set("Content-Type", "application/json")
	resp, e := cl.Do(req)
	if e != nil {
		row.Error = e.Error()
		row.ErrorClass = "transport"
		return
	}
	row.ServerHeaders = make(map[string][]string)
	for name, values := range resp.Header {
		if strings.HasPrefix(strings.ToLower(name), "x-r8-") {
			row.ServerHeaders[name] = append([]string(nil), values...)
		}
	}
	var replayErr error
	row.Replay, replayErr = strconv.ParseBool(resp.Header.Get("X-R8-Replay"))
	if replayErr != nil {
		row.Error = "invalid or missing X-R8-Replay"
	}
	if resp.ProtoMajor != 1 {
		row.Error = "response did not use HTTP/1.x"
	}
	if resp.ContentLength > maxWire {
		resp.Body.Close()
		row.Error = "response body exceeds frame limit"
		return
	}
	bodyReadStart := time.Now()
	raw, readErr := io.ReadAll(io.LimitReader(resp.Body, maxWire+1))
	bodyReadEnd := time.Now()
	row.BodyReadNS = bodyReadEnd.Sub(bodyReadStart).Nanoseconds()
	if readErr == nil {
		row.BodyCompleteOffsetNS = bodyReadEnd.Sub(epoch).Nanoseconds()
	}
	responseRaw = raw
	closeErr := resp.Body.Close()
	row.BodyBytes = len(raw)
	if readErr != nil {
		row.Error = "read response: " + readErr.Error()
		row.ErrorClass = "transport"
		return
	}
	if closeErr != nil {
		row.Error = "close response: " + closeErr.Error()
		row.ErrorClass = "transport"
		return
	}
	if len(raw) > maxWire {
		row.Error = "response body exceeds frame limit"
		return
	}
	if resp.StatusCode != http.StatusOK {
		row.Error = fmt.Sprintf("HTTP status %d", resp.StatusCode)
		row.ErrorClass = "http"
		return
	}
	if resp.ContentLength < 0 || resp.ContentLength != int64(len(raw)) {
		row.Error = "missing or inconsistent response Content-Length"
		return
	}
	if resp.Header.Get("Content-Encoding") != "" {
		row.Error = "unexpected Content-Encoding"
		return
	}
	if row.Error != "" {
		return
	}
	for _, h := range []struct {
		name string
		dst  *int64
	}{{"X-R8-Queue-Ns", &row.ServerQueueNS}, {"X-R8-Proof-Ns", &row.ServerProofNS}, {"X-R8-Encode-Ns", &row.ServerEncodeNS}} {
		n, err := strconv.ParseInt(resp.Header.Get(h.name), 10, 64)
		if err != nil || n < 0 {
			row.Error = "invalid " + h.name
			return
		}
		*h.dst = n
	}
	decodeStart := time.Now()
	restored, decodeErr := decodeResponseSafely(raw, c.Mode)
	if decodeErr != nil {
		row.Error = "decode response: " + decodeErr.Error()
	} else if !a.Accept(c.CaseID, batch, restored) {
		row.Error = "response root, ordered key/value binding, or native proof verification failed"
	}
	row.DecodeVerifyNS = time.Since(decodeStart).Nanoseconds()
	return
}

func fetchServerStats(c ClientConfig) (json.RawMessage, error) {
	cl, tr := newWorkerClient(c.Timeout)
	defer tr.CloseIdleConnections()
	resp, e := cl.Get(strings.TrimRight(c.URL, "/") + "/stats")
	if e != nil {
		return nil, e
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("stats HTTP status %d", resp.StatusCode)
	}
	raw, e := io.ReadAll(io.LimitReader(resp.Body, 1<<20+1))
	if e != nil {
		return nil, e
	}
	if len(raw) > 1<<20 {
		return nil, fmt.Errorf("stats body too large")
	}
	var obj map[string]any
	if e = strictJSON(raw, &obj); e != nil || obj == nil {
		return nil, fmt.Errorf("invalid stats response: %v", e)
	}
	return json.RawMessage(raw), nil
}

func nearestRank(v []int64, p float64) int64 {
	if len(v) == 0 {
		return 0
	}
	cp := append([]int64(nil), v...)
	sort.Slice(cp, func(i, j int) bool { return cp[i] < cp[j] })
	rank := int(math.Ceil(p * float64(len(cp))))
	if rank < 1 {
		rank = 1
	}
	if rank > len(cp) {
		rank = len(cp)
	}
	return cp[rank-1]
}

func measurementDrain(nominal, elapsed time.Duration) time.Duration {
	if elapsed > nominal {
		return elapsed - nominal
	}
	return 0
}

func summarizeClient(rows []ClientRecord, nominal, elapsed time.Duration) ClientSummary {
	s := ClientSummary{Schema: "round8-client-summary-v1", NominalNS: nominal.Nanoseconds(), AdmissionNS: nominal.Nanoseconds(), StopReason: "nominal_deadline", DurationNS: elapsed.Nanoseconds(), DrainNS: measurementDrain(nominal, elapsed).Nanoseconds(), ErrorCounts: map[string]int64{}, IntegrityOK: true, MeasurementComplete: true, LatencyMeaning: "conditional closed-loop verified end-to-end latency; successful requests only", LatencyMetric: "conditional closed-loop verified end-to-end request latency", ThroughputMeaning: "successful requests / actual elapsed time from admission start through all admitted request completions; includes send/body read/decode/binding/native verification", QuantileMethod: "nearest-rank ceil(p*n); p50=.50,p95=.95,p99=.99; successful requests only"}
	lat := make([]int64, 0, len(rows))
	for _, row := range rows {
		s.Attempted++
		if row.Completion && row.EndOffsetNS > nominal.Nanoseconds() {
			s.DrainCompletions++
		}
		s.RawSums.LatencyNS += row.LatencyNS
		s.RawSums.DecodeVerifyNS += row.DecodeVerifyNS
		s.RawSums.ServerQueueNS += row.ServerQueueNS
		s.RawSums.ServerProofNS += row.ServerProofNS
		s.RawSums.ServerEncodeNS += row.ServerEncodeNS
		s.Bytes.RequestBodySum += int64(row.RequestBodyBytes)
		s.Bytes.ResponseBodySum += int64(row.BodyBytes)
		if row.Success && row.Completion && row.Error == "" {
			s.Success++
			if row.EndOffsetNS <= nominal.Nanoseconds() {
				s.FixedWindowVerifiedSuccess++
			}
			lat = append(lat, row.LatencyNS)
			if s.Success == 1 || row.BodyBytes < s.Bytes.ResponseBodyMin {
				s.Bytes.ResponseBodyMin = row.BodyBytes
			}
			if row.BodyBytes > s.Bytes.ResponseBodyMax {
				s.Bytes.ResponseBodyMax = row.BodyBytes
			}
		} else {
			s.Errors++
			s.IntegrityOK = false
			s.ErrorCounts[row.ErrorClass]++
		}
	}
	s.LatencyNS = ClientQuantiles{nearestRank(lat, .5), nearestRank(lat, .95), nearestRank(lat, .99), nearestRank(lat, 1)}
	if elapsed > 0 {
		s.ThroughputSuccessPerSec = float64(s.Success) / elapsed.Seconds()
	}
	if nominal > 0 {
		s.NominalSuccessPerSec = float64(s.Success) / nominal.Seconds()
		s.AdmissionSuccessPerSec = s.NominalSuccessPerSec
		s.FixedWindowThroughputSuccessPerSec = float64(s.FixedWindowVerifiedSuccess) / nominal.Seconds()
	}
	s.PrimaryThroughputMetric = "fixed_window_throughput_success_per_sec: successful proof-verified, archive-matched requests whose verification endpoint is within the nominal admission window / nominal seconds"
	return s
}

func writeClientRows(path string, rows []ClientRecord) error {
	f, e := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
	if e != nil {
		return e
	}
	enc := json.NewEncoder(f)
	for _, row := range rows {
		if e = enc.Encode(row); e != nil {
			f.Close()
			return e
		}
	}
	if e = f.Sync(); e != nil {
		f.Close()
		return e
	}
	return f.Close()
}

func RunClient(c ClientConfig, a *Archive) error {
	if e := c.validate(); e != nil {
		return e
	}
	bodies, e := clientBodies(c, a)
	if e != nil {
		return e
	}
	lengths := []int{len(bodies[0]), len(bodies[1]), len(bodies[2])}
	if e = writeJSON(filepath.Join(c.WorkDir, "config.json"), map[string]any{"schema": "round8-client-config-v1", "client": c, "request_body_bytes_by_batch": lengths, "connection_policy": "one sequential HTTP/1.1 persistent connection per client loop; one verified request minimum per loop in warmup; establishment excluded", "clock": "Go time.Now/Time.Sub monotonic nanoseconds", "admission_policy": "closed-loop; stop new admissions on first integrity failure and drain admitted requests; transport/status errors continue nominal window; every attempt retained", "request_retries": 0, "batch_rotation": "(worker + seq) modulo 3, in warmup and measurement", "primary_throughput_metric": "fixed_window_throughput_success_per_sec", "archive_frame_gate": "exact archived frame bytes checked after verification latency endpoint; this work remains in closed-loop scheduling and actual elapsed time"}); e != nil {
		return e
	}
	if e = writeJSON(filepath.Join(c.WorkDir, "environment.json"), Environment(a)); e != nil {
		return e
	}
	clients := make([]*http.Client, c.Concurrency)
	transports := make([]*http.Transport, c.Concurrency)
	for i := range clients {
		clients[i], transports[i] = newWorkerClient(c.Timeout)
		defer transports[i].CloseIdleConnections()
	}
	warmRows := make([][]ClientRecord, c.Concurrency)
	var wg sync.WaitGroup
	warmEpoch := time.Now()
	warmEnd := warmEpoch.Add(c.Warmup)
	var warmStop atomic.Bool
	for i := range clients {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			for seq := int64(0); ; seq++ {
				if warmStop.Load() || (seq > 0 && !time.Now().Before(warmEnd)) {
					return
				}
				batch := (i + int(seq)) % 3
				row := performClientRequest(context.Background(), clients[i], c, a, i, seq, batch, bodies[batch], warmEpoch)
				warmRows[i] = append(warmRows[i], row)
				if !row.Success {
					warmStop.Store(true)
					return
				}
			}
		}(i)
	}
	wg.Wait()
	warm := ClientCounts{}
	var warmErrors []ClientRecord
	for _, rows := range warmRows {
		for _, row := range rows {
			warm.Attempted++
			if row.Success {
				warm.Success++
			} else {
				warm.Errors++
				warmErrors = append(warmErrors, row)
			}
		}
	}
	if e = writeJSON(filepath.Join(c.WorkDir, "warmup.json"), map[string]any{"schema": "round8-client-warmup-v1", "counts": warm, "errors": warmErrors, "actual_ns": time.Since(warmEpoch).Nanoseconds(), "requested_ns": c.Warmup.Nanoseconds(), "minimum_requests_per_worker": 1}); e != nil {
		return e
	}
	var allWarmRows []ClientRecord
	for _, rows := range warmRows {
		allWarmRows = append(allWarmRows, rows...)
	}
	if e = writeClientRows(filepath.Join(c.WorkDir, "warmup_log.jsonl"), allWarmRows); e != nil {
		return e
	}
	if warm.Errors != 0 {
		if e = writeJSON(filepath.Join(c.WorkDir, "completion.json"), map[string]any{"schema": "round8-client-completion-v1", "complete": false, "recording_complete": true, "integrity_ok": false, "stop_reason": "warmup_failure", "warmup": warm, "warmup_attempted": warm.Attempted, "warmup_success": warm.Success, "warmup_errors": warm.Errors, "attempted": 0, "success": 0, "errors": 0}); e != nil {
			return e
		}
		return fmt.Errorf("verified warmup failed: %d errors", warm.Errors)
	}
	statsBefore, e := fetchServerStats(c)
	if e != nil {
		return fmt.Errorf("before measurement stats: %w", e)
	}
	workerRows := make([][]ClientRecord, c.Concurrency)
	for i := range workerRows {
		workerRows[i] = make([]ClientRecord, 0, 1024)
	}
	memBefore := clientMemorySnapshot()
	procBefore := procSnapshot()
	startGate := make(chan struct{})
	var start time.Time
	var integrityStop atomic.Bool
	var integrityStopNS atomic.Int64
	var stopOnce sync.Once
	for i := range clients {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			<-startGate
			deadline := start.Add(c.Duration)
			rows := workerRows[i]
			for seq := int64(0); ; seq++ {
				admitted := time.Now()
				if integrityStop.Load() || !admitted.Before(deadline) {
					break
				}
				batch := (i + int(seq)) % 3
				row := performClientRequestAt(context.Background(), clients[i], c, a, i, seq, batch, bodies[batch], start, admitted)
				rows = append(rows, row)
				if row.ErrorClass == "integrity" {
					stopOnce.Do(func() { integrityStopNS.Store(time.Since(start).Nanoseconds()); integrityStop.Store(true) })
				}
			}
			workerRows[i] = rows
		}(i)
	}
	start = time.Now()
	close(startGate)
	wg.Wait()
	end := time.Now()
	elapsed := end.Sub(start)
	// The end timestamp precedes all post-measurement snapshots and file writing.
	memAfter := clientMemorySnapshot()
	procAfter := procSnapshot()
	statsAfter, statsErr := fetchServerStats(c)
	var rows []ClientRecord
	for _, r := range workerRows {
		rows = append(rows, r...)
	}
	sort.Slice(rows, func(i, j int) bool {
		if rows[i].StartOffsetNS == rows[j].StartOffsetNS {
			return rows[i].Worker < rows[j].Worker
		}
		return rows[i].StartOffsetNS < rows[j].StartOffsetNS
	})
	if e = writeClientRows(filepath.Join(c.WorkDir, "log.jsonl"), rows); e != nil {
		return e
	}
	summary := summarizeClient(rows, c.Duration, elapsed)
	summary.Warmup = warm
	summary.ClientMemBefore = memBefore
	summary.ClientMemAfter = memAfter
	summary.ClientProcBefore = procBefore
	summary.ClientProcAfter = procAfter
	summary.ServerStatsBefore = statsBefore
	summary.ServerStatsAfter = statsAfter
	summary.AdmissionStartUTC = start.UTC().Format(time.RFC3339Nano)
	summary.MeasurementEndUTC = end.UTC().Format(time.RFC3339Nano)
	var beforeReplay, afterReplay struct {
		Replay *bool `json:"replay"`
	}
	beforeReplayErr := json.Unmarshal(statsBefore, &beforeReplay)
	afterReplayErr := json.Unmarshal(statsAfter, &afterReplay)
	replayMismatch := beforeReplayErr != nil || afterReplayErr != nil || beforeReplay.Replay == nil || afterReplay.Replay == nil
	if !replayMismatch {
		summary.ServerReplay = *beforeReplay.Replay
		replayMismatch = *beforeReplay.Replay != *afterReplay.Replay
	}
	if !replayMismatch {
		for _, row := range rows {
			if row.Success && row.Replay != summary.ServerReplay {
				replayMismatch = true
				break
			}
		}
	}
	if replayMismatch {
		summary.MeasurementComplete = false
		summary.IntegrityOK = false
		summary.StopReason = "server_replay_mismatch"
	}
	if integrityStop.Load() {
		summary.StopReason = "integrity_failure"
		summary.MeasurementComplete = false
		summary.IntegrityOK = false
		summary.AdmissionNS = integrityStopNS.Load()
		if summary.AdmissionNS > summary.NominalNS {
			summary.AdmissionNS = summary.NominalNS
		}
		summary.DrainNS = measurementDrain(time.Duration(summary.AdmissionNS), elapsed).Nanoseconds()
		if summary.AdmissionNS > 0 {
			summary.AdmissionSuccessPerSec = float64(summary.Success) / (float64(summary.AdmissionNS) / float64(time.Second))
		}
	}
	if statsErr != nil {
		summary.MeasurementComplete = false
		summary.IntegrityOK = false
	}
	if e = writeJSON(filepath.Join(c.WorkDir, "summary.json"), summary); e != nil {
		return e
	}
	if statsErr != nil {
		return fmt.Errorf("after measurement stats: %w", statsErr)
	}
	if e = writeJSON(filepath.Join(c.WorkDir, "completion.json"), map[string]any{"schema": "round8-client-completion-v1", "complete": summary.MeasurementComplete, "recording_complete": true, "integrity_ok": summary.IntegrityOK, "stop_reason": summary.StopReason, "attempted": summary.Attempted, "success": summary.Success, "errors": summary.Errors, "utc": time.Now().UTC().Format(time.RFC3339Nano)}); e != nil {
		return e
	}
	if integrityStop.Load() {
		return fmt.Errorf("measurement stopped after frame or proof integrity failure")
	}
	if replayMismatch {
		return fmt.Errorf("server replay state missing or inconsistent across measurement")
	}
	return nil
}
