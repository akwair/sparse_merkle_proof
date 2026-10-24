package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"math/rand"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

const diagnosticBatchOperations = 32
const diagnosticRepeats = 5
const diagnosticExpectedRows = 540
const diagnosticSeed = 3407

type DiagnosticCase struct {
	ID           string `json:"id"`
	Q            int    `json:"q"`
	Distribution string `json:"distribution"`
}

var diagnosticCases = []DiagnosticCase{
	{"dev_n16384_q1_v32_member_uniform_b0", 1, "uniform"},
	{"dev_n16384_q128_v32_member_uniform_b0", 128, "uniform"},
	{"dev_n16384_q1_v32_member_zipf_b0", 1, "zipf"},
	{"dev_n16384_q128_v32_member_zipf_b0", 128, "zipf"},
}

type DiagnosticStep struct {
	DiagnosticCase
	Stage    string `json:"stage"`
	Mode     string `json:"mode"`
	Repeat   int    `json:"repeat"`
	Order    int    `json:"order"`
	Sequence int    `json:"sequence"`
}

type DiagnosticRow struct {
	DiagnosticStep
	BatchOperations     int     `json:"batch_operations"`
	AllocatedBytes      uint64  `json:"allocated_bytes"`
	Mallocs             uint64  `json:"mallocs"`
	Frees               uint64  `json:"frees"`
	NumGC               uint64  `json:"num_gc"`
	PauseNS             uint64  `json:"pause_ns"`
	BytesPerOperation   float64 `json:"bytes_per_operation"`
	MallocsPerOperation float64 `json:"mallocs_per_operation"`
}

type DiagnosticFixture struct {
	Bundle   Bundle
	Frames   map[string][]byte
	Restored map[string]Bundle
}

type DiagnosticOutput struct {
	Wire     []byte
	Bundle   Bundle
	Verified bool
}

func validateDiagnosticRequest(stage, mode string, batch int) error {
	if stage != "encode" && stage != "decode" && stage != "verify" {
		return fmt.Errorf("unknown diagnostic stage %q", stage)
	}
	validMode := false
	for _, m := range studyModes {
		if mode == m {
			validMode = true
			break
		}
	}
	if !validMode {
		return fmt.Errorf("unknown diagnostic mode %q", mode)
	}
	if batch != diagnosticBatchOperations {
		return fmt.Errorf("batch operations must be %d", diagnosticBatchOperations)
	}
	return nil
}

func diagnosticPlan() []DiagnosticStep {
	rng := rand.New(rand.NewSource(diagnosticSeed))
	plan := make([]DiagnosticStep, 0, diagnosticExpectedRows)
	for _, c := range diagnosticCases {
		for rep := 0; rep < diagnosticRepeats; rep++ {
			for _, stage := range []string{"encode", "decode", "verify"} {
				for order, mi := range rng.Perm(len(studyModes)) {
					plan = append(plan, DiagnosticStep{DiagnosticCase: c, Stage: stage, Mode: studyModes[mi], Repeat: rep, Order: order, Sequence: len(plan)})
				}
			}
		}
	}
	return plan
}

func validateDiagnosticBundle(b Bundle, expectedQ int) error {
	if len(b.Root) != 32 || len(b.Items) < 1 || len(b.Items) > 256 || (expectedQ > 0 && len(b.Items) != expectedQ) {
		return fmt.Errorf("invalid native bundle shape or query count")
	}
	for _, it := range b.Items {
		if len(it.Key) != 32 || len(it.Value) != 32 || len(it.Proof.SideNodes) > 256 || len(it.Proof.NonMembershipLeafData) > 65 || len(it.Proof.SiblingData) > 65 {
			return fmt.Errorf("invalid native item shape")
		}
		for _, node := range it.Proof.SideNodes {
			if len(node) != 32 {
				return fmt.Errorf("invalid native side-node shape")
			}
		}
	}
	if !verify(b) {
		return fmt.Errorf("native proof verification failed")
	}
	return nil
}

func prepareDiagnosticFixture(b Bundle) (*DiagnosticFixture, error) {
	if err := validateDiagnosticBundle(b, 0); err != nil {
		return nil, err
	}
	f := &DiagnosticFixture{Bundle: b, Frames: make(map[string][]byte), Restored: make(map[string]Bundle)}
	encoder := NewEncoder()
	for _, mode := range studyModes {
		wire, err := encoder.Encode(b, mode)
		if err != nil {
			return nil, fmt.Errorf("reference encode %s: %w", mode, err)
		}
		restored, err := decodeStudy(wire, mode)
		if err != nil {
			return nil, fmt.Errorf("reference decode %s: %w", mode, err)
		}
		if !equalBundle(b, restored) || !verify(restored) {
			return nil, fmt.Errorf("reference restoration %s", mode)
		}
		f.Frames[mode], f.Restored[mode] = wire, restored
		if strings.HasPrefix(mode, "reset-") && !bytes.Equal(wire, f.Frames[strings.TrimPrefix(mode, "reset-")]) {
			return nil, fmt.Errorf("fresh/reset reference identity %s", mode)
		}
	}
	return f, nil
}

func loadDiagnosticBundle(dir string, c DiagnosticCase) (Bundle, error) {
	knownCase := false
	for _, expected := range diagnosticCases {
		if c == expected {
			knownCase = true
			break
		}
	}
	if !knownCase {
		return Bundle{}, fmt.Errorf("unregistered diagnostic case %q", c.ID)
	}
	p := filepath.Join(dir, c.ID, "bundle.json")
	f, err := os.Open(p)
	if err != nil {
		return Bundle{}, err
	}
	defer f.Close()
	info, err := f.Stat()
	if err != nil {
		return Bundle{}, err
	}
	if !info.Mode().IsRegular() || info.Size() > 16*1024*1024 {
		return Bundle{}, fmt.Errorf("invalid input file size/type: %s", p)
	}
	dec := json.NewDecoder(f)
	dec.DisallowUnknownFields()
	var b Bundle
	if err := dec.Decode(&b); err != nil {
		return Bundle{}, fmt.Errorf("input JSON %s: %w", p, err)
	}
	var trailing any
	if err := dec.Decode(&trailing); err != io.EOF {
		return Bundle{}, fmt.Errorf("trailing input JSON: %s", p)
	}
	if err := validateDiagnosticBundle(b, c.Q); err != nil {
		return Bundle{}, fmt.Errorf("input %s: %w", p, err)
	}
	return b, nil
}

// All fixtures, reference frames, and writer priming precede the counter window.
// ReadMemStats measures process-wide allocation/GC deltas; this is not a timer.
func measureDiagnosticStage(f *DiagnosticFixture, s DiagnosticStep, batch int) (DiagnosticRow, DiagnosticOutput, error) {
	var row DiagnosticRow
	var out DiagnosticOutput
	if err := validateDiagnosticRequest(s.Stage, s.Mode, batch); err != nil {
		return row, out, err
	}
	if f == nil {
		return row, out, fmt.Errorf("missing diagnostic fixture")
	}
	reference, exists := f.Frames[s.Mode]
	if !exists || len(reference) == 0 {
		return row, out, fmt.Errorf("missing reference frame")
	}
	restored, exists := f.Restored[s.Mode]
	if !exists || len(restored.Items) == 0 {
		return row, out, fmt.Errorf("missing restored bundle")
	}
	encoder := NewEncoder()
	if s.Stage == "encode" && strings.HasPrefix(s.Mode, "reset-") {
		primed, err := encoder.Encode(f.Bundle, s.Mode)
		if err != nil {
			return row, out, fmt.Errorf("writer priming: %w", err)
		}
		if !bytes.Equal(primed, reference) {
			return row, out, fmt.Errorf("writer priming frame mismatch")
		}
	}
	var before, after runtime.MemStats
	var err error
	runtime.GC()
	runtime.ReadMemStats(&before)
	// Only the selected stage and its error/boolean check execute in these loops.
	// In particular, verify uses the once-restored bundle, not a per-call decode.
	switch s.Stage {
	case "encode":
		for i := 0; i < batch; i++ {
			out.Wire, err = encoder.Encode(f.Bundle, s.Mode)
			if err != nil {
				return row, out, fmt.Errorf("encode operation %d: %w", i, err)
			}
		}
	case "decode":
		for i := 0; i < batch; i++ {
			out.Bundle, err = decodeStudy(reference, s.Mode)
			if err != nil {
				return row, out, fmt.Errorf("decode operation %d: %w", i, err)
			}
		}
	case "verify":
		for i := 0; i < batch; i++ {
			out.Verified = verify(restored)
			if !out.Verified {
				return row, out, fmt.Errorf("verify operation %d failed", i)
			}
		}
	}
	runtime.ReadMemStats(&after)
	runtime.KeepAlive(f)
	runtime.KeepAlive(reference)
	runtime.KeepAlive(restored)
	runtime.KeepAlive(encoder)
	runtime.KeepAlive(out)
	if after.TotalAlloc < before.TotalAlloc || after.Mallocs < before.Mallocs || after.Frees < before.Frees || after.NumGC < before.NumGC || after.PauseTotalNs < before.PauseTotalNs {
		return row, out, fmt.Errorf("memory counter decreased or overflowed")
	}
	// Output checks are intentionally after both memory snapshots.
	switch s.Stage {
	case "encode":
		if !bytes.Equal(out.Wire, reference) {
			return row, out, fmt.Errorf("final encoded frame mismatch")
		}
		decoded, err := decodeStudy(out.Wire, s.Mode)
		if err != nil || !equalBundle(decoded, f.Bundle) || !verify(decoded) {
			return row, out, fmt.Errorf("final encoded frame restoration failed: %v", err)
		}
	case "decode":
		if !equalBundle(out.Bundle, f.Bundle) || !verify(out.Bundle) {
			return row, out, fmt.Errorf("final decoded bundle invalid")
		}
	case "verify":
		if !out.Verified || !equalBundle(restored, f.Bundle) {
			return row, out, fmt.Errorf("final verified bundle mismatch")
		}
	}
	row = DiagnosticRow{
		DiagnosticStep: s, BatchOperations: batch,
		AllocatedBytes: after.TotalAlloc - before.TotalAlloc,
		Mallocs:        after.Mallocs - before.Mallocs, Frees: after.Frees - before.Frees,
		NumGC: uint64(after.NumGC - before.NumGC), PauseNS: after.PauseTotalNs - before.PauseTotalNs,
	}
	row.BytesPerOperation = float64(row.AllocatedBytes) / float64(batch)
	row.MallocsPerOperation = float64(row.Mallocs) / float64(batch)
	return row, out, nil
}

func writeDiagnosticJSON(path string, value any) error {
	f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
	if err != nil {
		return err
	}
	defer f.Close()
	enc := json.NewEncoder(f)
	enc.SetIndent("", "  ")
	if err := enc.Encode(value); err != nil {
		return err
	}
	if err := f.Sync(); err != nil {
		return err
	}
	return f.Close()
}

func runDiagnostic(args []string) error {
	if len(args) != 2 || strings.TrimSpace(args[0]) == "" || strings.TrimSpace(args[1]) == "" {
		return fmt.Errorf("usage: diagnostic_runner INPUT_DIR NEW_WORK_DIR")
	}
	inputDir, work := args[0], args[1]
	if err := os.Mkdir(work, 0755); err != nil {
		return err
	}
	if runtime.GOMAXPROCS(0) != 8 {
		return fmt.Errorf("diagnostic requires inherited GOMAXPROCS=8")
	}
	if runtime.Version() != "go1.27.3" {
		return fmt.Errorf("diagnostic requires go1.27.3, got %s", runtime.Version())
	}
	plan := diagnosticPlan()
	if len(plan) != diagnosticExpectedRows {
		return fmt.Errorf("unexpected plan count %d", len(plan))
	}
	fixtures := make(map[string]*DiagnosticFixture, len(diagnosticCases))
	for _, c := range diagnosticCases {
		b, err := loadDiagnosticBundle(inputDir, c)
		if err != nil {
			return err
		}
		fixture, err := prepareDiagnosticFixture(b)
		if err != nil {
			return fmt.Errorf("fixture %s: %w", c.ID, err)
		}
		fixtures[c.ID] = fixture
	}
	host, err := os.Hostname()
	if err != nil {
		return err
	}
	gogc, gogcSet := os.LookupEnv("GOGC")
	memlimit, memlimitSet := os.LookupEnv("GOMEMLIMIT")
	godebug, godebugSet := os.LookupEnv("GODEBUG")
	env := map[string]any{
		"kind": "separate_stage_allocation_diagnostic", "go": runtime.Version(),
		"os": runtime.GOOS, "arch": runtime.GOARCH, "hostname": host,
		"pid": os.Getpid(), "cpus": runtime.NumCPU(), "gomaxprocs": runtime.GOMAXPROCS(0),
		"gogc_env": gogc, "gogc_env_set": gogcSet, "gomemlimit_env": memlimit, "gomemlimit_env_set": memlimitSet,
		"godebug_env": godebug, "godebug_env_set": godebugSet,
		"seed": diagnosticSeed, "repeats": diagnosticRepeats, "batch_operations": diagnosticBatchOperations,
		"expected_rows": diagnosticExpectedRows, "expected_operations": diagnosticExpectedRows * diagnosticBatchOperations,
		"case_order": diagnosticCases, "stages": []string{"encode", "decode", "verify"}, "modes": studyModes,
		"execution_order": plan, "index_base": 0, "input_dir": inputDir,
		"utc":            time.Now().UTC().Format(time.RFC3339Nano),
		"counter_scope":  "process-wide runtime.MemStats deltas around 32 calls to one selected stage",
		"gc_policy":      "runtime.GC before each before-snapshot; no forced GC in batch; no GOGC changes",
		"reset_priming":  "one unmeasured encode before GC for each reset encode batch; other stages do not encode",
		"interpretation": "allocation diagnostic only; no latency estimate or GC-caused-latency claim",
	}
	if err := writeDiagnosticJSON(filepath.Join(work, "env.json"), env); err != nil {
		return err
	}
	log, err := os.OpenFile(filepath.Join(work, "log.jsonl"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
	if err != nil {
		return err
	}
	defer log.Close()
	enc := json.NewEncoder(log)
	rows, operations := 0, 0
	for _, step := range plan {
		row, _, err := measureDiagnosticStage(fixtures[step.ID], step, diagnosticBatchOperations)
		if err != nil {
			return fmt.Errorf("row %d %s/%s/%s: %w", step.Sequence, step.ID, step.Stage, step.Mode, err)
		}
		if err := enc.Encode(row); err != nil {
			return err
		}
		rows++
		operations += row.BatchOperations
	}
	runtime.KeepAlive(fixtures)
	if rows != diagnosticExpectedRows || operations != diagnosticExpectedRows*diagnosticBatchOperations {
		return fmt.Errorf("diagnostic row/operation count mismatch")
	}
	if err := log.Sync(); err != nil {
		return err
	}
	if err := log.Close(); err != nil {
		return err
	}
	return writeDiagnosticJSON(filepath.Join(work, "completion.json"), map[string]any{
		"complete": true, "rows": rows, "expected_rows": diagnosticExpectedRows,
		"operations": operations, "expected_operations": diagnosticExpectedRows * diagnosticBatchOperations,
		"batch_operations": diagnosticBatchOperations, "utc": time.Now().UTC().Format(time.RFC3339Nano),
	})
}

func main() {
	if err := runDiagnostic(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, "diagnostic:", err)
		os.Exit(1)
	}
}
