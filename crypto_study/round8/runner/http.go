package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"runtime"
	"sort"
	"strconv"
	"sync/atomic"
	"time"
)

type readRequest struct {
	CaseID string   `json:"case_id"`
	Batch  *int     `json:"batch"`
	Mode   string   `json:"mode"`
	Keys   [][]byte `json:"keys"`
}
type Service struct {
	archive                                             *Archive
	pool                                                chan *Worker
	replay                                              bool
	frames                                              map[string]map[int]map[string][]byte
	probe                                               []byte
	requests, errors, bytes, queueNS, proofNS, encodeNS atomic.Uint64
}
type MemorySnapshot struct {
	HeapAlloc    uint64 `json:"heap_alloc"`
	HeapSys      uint64 `json:"heap_sys"`
	TotalAlloc   uint64 `json:"total_alloc"`
	NumGC        uint32 `json:"num_gc"`
	PauseTotalNS uint64 `json:"pause_total_ns"`
}

func memorySnapshot() MemorySnapshot {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	return MemorySnapshot{m.HeapAlloc, m.HeapSys, m.TotalAlloc, m.NumGC, m.PauseTotalNs}
}

type ServiceStats struct {
	Requests uint64            `json:"requests"`
	Errors   uint64            `json:"errors"`
	Bytes    uint64            `json:"bytes"`
	QueueNS  uint64            `json:"queue_ns"`
	ProofNS  uint64            `json:"proof_ns"`
	EncodeNS uint64            `json:"encode_ns"`
	Workers  int               `json:"workers"`
	Replay   bool              `json:"replay"`
	Memory   MemorySnapshot    `json:"memory"`
	Proc     map[string]string `json:"proc"`
	UTC      string            `json:"utc"`
}

func procSnapshot() map[string]string {
	out := map[string]string{}
	for _, name := range []string{"stat", "status", "io"} {
		if b, e := os.ReadFile("/proc/self/" + name); e == nil {
			out[name] = string(b)
		}
	}
	return out
}
func NewService(a *Archive, n int, replay bool) (*Service, error) {
	if n < 1 || n > 1024 {
		return nil, fmt.Errorf("workers must be in [1,1024]")
	}
	s := &Service{archive: a, pool: make(chan *Worker, n), replay: replay, probe: make([]byte, 4<<20)}
	for i := range s.probe {
		s.probe[i] = byte(i)
	}
	ids := make([]string, 0, len(a.cases))
	for id := range a.cases {
		ids = append(ids, id)
	}
	sort.Strings(ids)
	if len(ids) == 0 {
		return nil, fmt.Errorf("empty archive")
	}
	firstID := ids[0]
	for i := 0; i < n; i++ {
		w, e := a.NewWorker()
		if e != nil {
			return nil, e
		}
		for _, m := range []string{"reset-zlib-ordinary", "reset-zlib-compact", "reset-zlib-dictionary"} {
			if _, _, e = w.Serve(firstID, 0, m); e != nil {
				return nil, e
			}
		}
		s.pool <- w
	}
	if replay {
		s.frames = map[string]map[int]map[string][]byte{}
		w, e := a.NewWorker()
		if e != nil {
			return nil, e
		}
		for id := range a.cases {
			s.frames[id] = map[int]map[string][]byte{}
			for b := 0; b < 3; b++ {
				s.frames[id][b] = map[string][]byte{}
				for _, m := range studyModes {
					raw, _, e := w.Serve(id, b, m)
					if e != nil {
						return nil, e
					}
					s.frames[id][b][m] = raw
				}
			}
		}
	}
	return s, nil
}
func (s *Service) Stats() ServiceStats {
	return ServiceStats{Requests: s.requests.Load(), Errors: s.errors.Load(), Bytes: s.bytes.Load(), QueueNS: s.queueNS.Load(), ProofNS: s.proofNS.Load(), EncodeNS: s.encodeNS.Load(), Workers: cap(s.pool), Replay: s.replay, Memory: memorySnapshot(), Proc: procSnapshot(), UTC: time.Now().UTC().Format(time.RFC3339Nano)}
}
func (s *Service) Handler() http.Handler {
	m := http.NewServeMux()
	m.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "GET" {
			s.errors.Add(1)
			http.Error(w, "method", 405)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		io.WriteString(w, `{"ready":true}`)
	})
	m.HandleFunc("/stats", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "GET" {
			s.errors.Add(1)
			http.Error(w, "method", 405)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(s.Stats())
	})
	m.HandleFunc("/probe", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "GET" {
			s.errors.Add(1)
			http.Error(w, "method", 405)
			return
		}
		n, e := strconv.Atoi(r.URL.Query().Get("bytes"))
		if e != nil || n < 0 || n > len(s.probe) {
			s.errors.Add(1)
			http.Error(w, "invalid bytes", 400)
			return
		}
		w.Header().Set("Content-Type", "application/octet-stream")
		w.Header().Set("Content-Length", strconv.Itoa(n))
		w.Header().Set("X-R8-Diagnostic", "probe")
		if _, e = w.Write(s.probe[:n]); e != nil {
			s.errors.Add(1)
		}
	})
	m.HandleFunc("/read", s.read)
	m.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) { s.errors.Add(1); http.NotFound(w, r) })
	return m
}
func (s *Service) read(w http.ResponseWriter, r *http.Request) {
	s.requests.Add(1)
	failed := true
	defer func() {
		if failed {
			s.errors.Add(1)
		}
	}()
	if r.Method != "POST" {
		http.Error(w, "method", 405)
		return
	}
	if r.ProtoMajor != 1 {
		http.Error(w, "HTTP/1.1 required", 400)
		return
	}
	if r.Header.Get("Content-Encoding") != "" {
		http.Error(w, "request encoding", 400)
		return
	}
	body, e := io.ReadAll(io.LimitReader(r.Body, 16385))
	if e != nil || len(body) > 16384 {
		http.Error(w, "request body limit", 400)
		return
	}
	var req readRequest
	if e = strictJSON(body, &req); e != nil || req.Batch == nil || !validMode(req.Mode) {
		http.Error(w, "invalid request", 400)
		return
	}
	keys, e := s.archive.RequestKeys(req.CaseID, *req.Batch)
	if e != nil || len(keys) != len(req.Keys) {
		http.Error(w, "invalid request binding", 400)
		return
	}
	for i, k := range keys {
		if !bytes.Equal(k, req.Keys[i]) {
			http.Error(w, "invalid request keys", 400)
			return
		}
	}
	queued := time.Now()
	var worker *Worker
	select {
	case worker = <-s.pool:
	case <-r.Context().Done():
		http.Error(w, "canceled", 408)
		return
	}
	st := ServerStages{QueueNS: time.Since(queued).Nanoseconds()}
	var raw []byte
	if s.replay {
		raw = s.frames[req.CaseID][*req.Batch][req.Mode]
	} else {
		var stages ServerStages
		raw, stages, e = worker.serveKeys(req.CaseID, *req.Batch, req.Mode, req.Keys)
		st.ProofNS = stages.ProofNS
		st.EncodeNS = stages.EncodeNS
	}
	s.pool <- worker
	if e != nil {
		http.Error(w, "native pipeline failed", 500)
		return
	}
	w.Header().Set("Content-Type", "application/octet-stream")
	w.Header().Set("Content-Length", strconv.Itoa(len(raw)))
	w.Header().Set("X-R8-Queue-Ns", strconv.FormatInt(st.QueueNS, 10))
	w.Header().Set("X-R8-Proof-Ns", strconv.FormatInt(st.ProofNS, 10))
	w.Header().Set("X-R8-Encode-Ns", strconv.FormatInt(st.EncodeNS, 10))
	w.Header().Set("X-R8-Replay", strconv.FormatBool(s.replay))
	n, e := w.Write(raw)
	if e != nil || n != len(raw) {
		return
	}
	s.bytes.Add(uint64(n))
	s.queueNS.Add(uint64(st.QueueNS))
	s.proofNS.Add(uint64(st.ProofNS))
	s.encodeNS.Add(uint64(st.EncodeNS))
	failed = false
}

func Environment(a *Archive) map[string]any {
	return map[string]any{"go": runtime.Version(), "os": runtime.GOOS, "arch": runtime.GOARCH, "cpus": runtime.NumCPU(), "gomaxprocs": runtime.GOMAXPROCS(0), "clock": "Go time.Now/time.Sub monotonic", "clock_frequency": timerFrequency, "data_root": a.root, "data_hashes": a.Hashes, "proc": procSnapshot(), "utc": time.Now().UTC().Format(time.RFC3339Nano)}
}
func writeJSON(path string, v any) error {
	raw, e := json.MarshalIndent(v, "", "  ")
	if e != nil {
		return e
	}
	return os.WriteFile(path, append(raw, '\n'), 0644)
}
