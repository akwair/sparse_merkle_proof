package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	stdhash "hash"
	"net/http"
	"net/http/httptest"
	"runtime"
	"strings"
	"sync"
	"sync/atomic"
	"testing"

	smt "github.com/celestiaorg/smt"
)

// Synthetic correctness fixtures are deliberately unrelated to archived formal data.
func fixtureArchive(t *testing.T) (*Archive, string) {
	t.Helper()
	cp := checkpoint{Domain: "dev", N: 12, ValueBytes: 32}
	for i := 0; i < cp.N; i++ {
		k := sha256.Sum256([]byte(fmt.Sprintf("fixture-key-%d", i)))
		v := sha256.Sum256([]byte(fmt.Sprintf("fixture-value-%d", i)))
		cp.Keys = append(cp.Keys, k[:])
		cp.Values = append(cp.Values, v[:])
	}
	ft, err := freezeCheckpoint(cp, false)
	if err != nil {
		t.Fatal(err)
	}
	id := "dev_n12_q3_v32_member_zipf"
	a := &Archive{trees: map[string]*FrozenTree{"fixture": ft}, cases: map[string]*archiveCase{id: {treeID: "fixture", batches: map[int][]int{0: {2, 2, 5}, 1: {4, 1, 4}, 2: {0, 11, 0}}}}, Hashes: map[string]string{}}
	populateFixtureReferences(t, a, id)
	return a, id
}
func populateFixtureReferences(t *testing.T, a *Archive, id string) {
	t.Helper()
	c := a.cases[id]
	c.references = map[int]map[string][]byte{}
	w, _ := a.NewWorker()
	for b := 0; b < 3; b++ {
		c.references[b] = map[string][]byte{}
		for _, mode := range studyModes {
			if strings.HasPrefix(mode, "reset-") {
				continue
			}
			raw, _, e := w.Serve(id, b, mode)
			if e != nil {
				t.Fatal(e)
			}
			c.references[b][mode] = raw
		}
	}
}

func TestWorkerModesBindingMultiplicityAndIsolation(t *testing.T) {
	a, id := fixtureArchive(t)
	w, err := a.NewWorker()
	if err != nil {
		t.Fatal(err)
	}
	real := w.trees["fixture"]
	counter := &countTree{inner: real}
	w.trees["fixture"] = counter
	for _, mode := range studyModes {
		raw, _, err := w.Serve(id, 0, mode)
		if err != nil {
			t.Fatal(err)
		}
		b, err := decodeStudy(raw, mode)
		if err != nil || !a.Accept(id, 0, b) {
			t.Fatalf("%s binding: %v", mode, err)
		}
		golden, err := NewEncoder().Encode(b, mode)
		if err != nil || !bytes.Equal(raw, golden) {
			t.Fatalf("mode %s changed bytes", mode)
		}
		before := append([]byte(nil), raw...)
		raw[4] ^= 1
		again, _, err := w.Serve(id, 0, mode)
		if err != nil || !bytes.Equal(before, again) {
			t.Fatal("emitted frame aliases storage")
		}
		b.Items[0].Value[0] ^= 1
		if a.Accept(id, 0, b) {
			t.Fatal("altered value accepted")
		}
	}
	if counter.get != 54 || counter.prove != 54 {
		t.Fatalf("duplicates must get+prove separately: %d/%d", counter.get, counter.prove)
	}
	raw, _, _ := w.Serve(id, 0, "ordinary")
	b, _ := decodeStudy(raw, "ordinary")
	b.Root[0] ^= 1
	if a.Accept(id, 0, b) {
		t.Fatal("wrong root accepted")
	}
	b.Root[0] ^= 1
	b.Items[0], b.Items[2] = b.Items[2], b.Items[0]
	if a.Accept(id, 0, b) {
		t.Fatal("swapped keys accepted")
	}
	if _, err := decodeStudy(raw[:len(raw)-1], "ordinary"); err == nil {
		t.Fatal("truncation accepted")
	}
	ft := a.trees["fixture"]
	if ft.nodes.Set([]byte("x"), []byte("y")) == nil || ft.values.Delete([]byte("x")) == nil {
		t.Fatal("frozen stores accepted write")
	}
}

type countTree struct {
	inner      treeReader
	get, prove int
}

func (c *countTree) Get(k []byte) ([]byte, error) { c.get++; return c.inner.Get(k) }
func (c *countTree) Prove(k []byte) (smt.SparseMerkleProof, error) {
	c.prove++
	return c.inner.Prove(k)
}

type overlapHash struct {
	stdhash.Hash
	busy    atomic.Bool
	overlap *atomic.Bool
}

func (h *overlapHash) Write(p []byte) (int, error) {
	if !h.busy.CompareAndSwap(false, true) {
		h.overlap.Store(true)
	}
	defer h.busy.Store(false)
	runtime.Gosched()
	return h.Hash.Write(p)
}
func (h *overlapHash) Reset() {
	if !h.busy.CompareAndSwap(false, true) {
		h.overlap.Store(true)
	}
	defer h.busy.Store(false)
	runtime.Gosched()
	h.Hash.Reset()
}
func (h *overlapHash) Sum(p []byte) []byte {
	if !h.busy.CompareAndSwap(false, true) {
		h.overlap.Store(true)
	}
	defer h.busy.Store(false)
	runtime.Gosched()
	return h.Hash.Sum(p)
}
func TestConcurrentWorkersMixedModes(t *testing.T) {
	a, id := fixtureArchive(t)
	base := a.trees["fixture"]
	cp := checkpoint{Domain: "confirm", N: len(base.keys), ValueBytes: 1000, Keys: base.keys}
	for i := range cp.Keys {
		cp.Values = append(cp.Values, bytes.Repeat([]byte{byte(i + 1)}, 1000))
	}
	other, e := freezeCheckpoint(cp, false)
	if e != nil {
		t.Fatal(e)
	}
	a.trees["other"] = other
	otherID := "confirm_n12_q3_v1000_member_zipf"
	a.cases[otherID] = &archiveCase{treeID: "other", batches: a.cases[id].batches}
	populateFixtureReferences(t, a, otherID)
	goldens := map[string]map[int]map[string][]byte{}
	reference, _ := a.NewWorker()
	for _, caseID := range []string{id, otherID} {
		goldens[caseID] = map[int]map[string][]byte{}
		for batch := 0; batch < 3; batch++ {
			goldens[caseID][batch] = map[string][]byte{}
			for _, mode := range studyModes {
				raw, _, e := reference.Serve(caseID, batch, mode)
				if e != nil {
					t.Fatal(e)
				}
				goldens[caseID][batch][mode] = raw
			}
		}
	}
	var overlap atomic.Bool
	factory := func() stdhash.Hash { return &overlapHash{Hash: sha256.New(), overlap: &overlap} }
	ws := make([]*Worker, 8)
	for i := range ws {
		ws[i], _ = a.newWorkerWithHash(factory)
	}
	barrier := make(chan struct{})
	errs := make(chan error, 8)
	var wg sync.WaitGroup
	for i, w := range ws {
		wg.Add(1)
		go func(i int, w *Worker) {
			defer wg.Done()
			<-barrier
			for j := 0; j < 27; j++ {
				mode := studyModes[j%len(studyModes)]
				caseID := id
				if (i+j)%2 == 1 {
					caseID = otherID
				}
				batch := (i + j) % 3
				raw, _, e := w.Serve(caseID, batch, mode)
				if e != nil {
					errs <- e
					return
				}
				if !bytes.Equal(raw, goldens[caseID][batch][mode]) {
					errs <- fmt.Errorf("concurrent frame changed bytes")
					return
				}
				b, e := decodeStudy(raw, mode)
				if e != nil || !a.Accept(caseID, batch, b) {
					errs <- fmt.Errorf("concurrent binding %v", e)
					return
				}
			}
		}(i, w)
	}
	close(barrier)
	wg.Wait()
	close(errs)
	for e := range errs {
		t.Error(e)
	}
	if overlap.Load() {
		t.Fatal("shared mutable hash")
	}
	for i := 1; i < len(ws); i++ {
		if ws[i].encoder == ws[0].encoder || ws[i].hashers[0] == ws[0].hashers[0] {
			t.Fatal("worker context shared")
		}
	}
}

func TestHTTPExactFrameAndRejectInput(t *testing.T) {
	a, id := fixtureArchive(t)
	s, err := NewService(a, 2, false)
	if err != nil {
		t.Fatal(err)
	}
	ts := httptest.NewServer(s.Handler())
	defer ts.Close()
	w, _ := a.NewWorker()
	golden, _, _ := w.Serve(id, 0, "dictionary")
	keys, _ := a.RequestKeys(id, 0)
	good, _ := json.Marshal(map[string]any{"case_id": id, "batch": 0, "mode": "dictionary", "keys": keys})
	for _, tc := range []struct {
		body   string
		status int
	}{{string(good), 200}, {`{"case_id":"../../x","batch":0,"mode":"ordinary"}`, 400}, {fmt.Sprintf(`{"case_id":%q,"batch":3,"mode":"ordinary"}`, id), 400}, {fmt.Sprintf(`{"case_id":%q,"batch":0,"mode":"invalid"}`, id), 400}, {fmt.Sprintf(`{"case_id":%q,"mode":"ordinary"}`, id), 400}, {`{"unknown":1}`, 400}, {strings.Repeat(" ", 16385), 400}} {
		resp, e := http.Post(ts.URL+"/read", "application/json", strings.NewReader(tc.body))
		if e != nil {
			t.Fatal(e)
		}
		var body bytes.Buffer
		body.ReadFrom(resp.Body)
		resp.Body.Close()
		if resp.StatusCode != tc.status {
			t.Fatalf("%s status %d", tc.body, resp.StatusCode)
		}
		if tc.status == 200 {
			if !bytes.Equal(body.Bytes(), golden) || resp.Header.Get("Content-Encoding") != "" || resp.ContentLength != int64(len(golden)) {
				t.Fatal("frame/HTTP encoding changed")
			}
			if resp.Header.Get("X-R8-Proof-Ns") == "" {
				t.Fatal("missing stages")
			}
		}
	}
	stats := s.Stats()
	if stats.Requests != 7 || stats.Errors != 6 || stats.Bytes != uint64(len(golden)) {
		t.Fatalf("stats %+v", stats)
	}
	replay, _ := NewService(a, 1, true)
	r := httptest.NewRecorder()
	replay.Handler().ServeHTTP(r, httptest.NewRequest("POST", "/read", bytes.NewReader(good)))
	if r.Code != 200 || !replay.Stats().Replay || r.Header().Get("X-R8-Proof-Ns") != "0" {
		t.Fatal("diagnostic replay")
	}
	probe := httptest.NewRecorder()
	s.Handler().ServeHTTP(probe, httptest.NewRequest("GET", "/probe?bytes=4096", nil))
	if probe.Code != 200 || probe.Body.Len() != 4096 || probe.Header().Get("X-R8-Diagnostic") != "probe" {
		t.Fatal("diagnostic probe")
	}
	probe = httptest.NewRecorder()
	s.Handler().ServeHTTP(probe, httptest.NewRequest("GET", "/probe?bytes=4194305", nil))
	if probe.Code != 400 {
		t.Fatal("oversized probe accepted")
	}
}

func TestCheckpointRejectsCorruptionAndKeysAreDetached(t *testing.T) {
	a, id := fixtureArchive(t)
	ft := a.trees["fixture"]
	cp := checkpoint{Domain: "dev", N: len(ft.keys), ValueBytes: 32, Keys: ft.keys, Values: ft.checkpointValues, Root: append([]byte(nil), ft.root...)}
	cp.Root[0] ^= 1
	if _, e := freezeCheckpoint(cp, true); e == nil {
		t.Fatal("wrong root rebuilt")
	}
	cp.Root[0] ^= 1
	cp.Keys = append([][]byte(nil), cp.Keys...)
	cp.Keys[1] = cp.Keys[0]
	if _, e := freezeCheckpoint(cp, true); e == nil {
		t.Fatal("duplicate checkpoint keys")
	}
	keys, _ := a.RequestKeys(id, 0)
	keys[0][0] ^= 1
	again, _ := a.RequestKeys(id, 0)
	if bytes.Equal(keys[0], again[0]) {
		t.Fatal("keys alias checkpoint")
	}
	w, _ := a.NewWorker()
	if _, _, e := w.serveKeys(id, 0, "ordinary", keys); e == nil {
		t.Fatal("wrong request keys accepted")
	}
}

func TestStrictJSONRejectsExtraUnknownAndTruncated(t *testing.T) {
	for _, input := range []string{`{"A":1} {"A":2}`, `{"A":1,"B":2}`, `{"A":`} {
		var out struct{ A int }
		if strictJSON([]byte(input), &out) == nil {
			t.Fatal("bad JSON accepted", input)
		}
	}
	var b Bundle
	if err := json.Unmarshal([]byte(`{"Root":null,"Items":null}`), &b); err != nil {
		t.Fatal(err)
	}
}
