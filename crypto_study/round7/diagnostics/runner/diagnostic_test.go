package main

import (
	"bufio"
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"runtime"
	"strings"
	"testing"

	smt "github.com/celestiaorg/smt"
)

func tinyDiagnosticBundle(t *testing.T, q int) Bundle {
	t.Helper()
	tree := smt.NewSparseMerkleTree(smt.NewSimpleMap(), smt.NewSimpleMap(), sha256.New())
	keys := [][]byte{hash("diag/test/key/a"), hash("diag/test/key/b"), hash("diag/test/key/c")}
	values := [][]byte{hash("diag/test/value/a"), hash("diag/test/value/b"), hash("diag/test/value/c")}
	for i := range keys {
		if _, err := tree.Update(keys[i], values[i]); err != nil {
			t.Fatal(err)
		}
	}
	b := Bundle{Root: tree.Root()}
	for i := 0; i < q; i++ {
		j := i % len(keys)
		p, err := tree.Prove(keys[j])
		if err != nil {
			t.Fatal(err)
		}
		b.Items = append(b.Items, Item{Key: keys[j], Value: values[j], Proof: p})
	}
	if !verify(b) {
		t.Fatal("invalid native test fixture")
	}
	return b
}

func TestDiagnosticRequestBoundaries(t *testing.T) {
	for _, stage := range []string{"encode", "decode", "verify"} {
		for _, mode := range studyModes {
			if err := validateDiagnosticRequest(stage, mode, 32); err != nil {
				t.Fatal(err)
			}
		}
	}
	for _, tc := range []struct {
		stage, mode string
		batch       int
	}{
		{"", "ordinary", 32}, {"total", "ordinary", 32},
		{"encode", "", 32}, {"encode", "unknown", 32},
		{"encode", "ordinary", 0}, {"encode", "ordinary", -1},
		{"encode", "ordinary", 1}, {"encode", "ordinary", 31}, {"encode", "ordinary", 33},
	} {
		if err := validateDiagnosticRequest(tc.stage, tc.mode, tc.batch); err == nil {
			t.Errorf("accepted invalid stage/mode/batch: %+v", tc)
		}
	}
}

func TestDiagnosticPlanCompleteDeterministic(t *testing.T) {
	p, again := diagnosticPlan(), diagnosticPlan()
	if len(p) != 540 || !reflect.DeepEqual(p, again) {
		t.Fatalf("plan length=%d or nondeterministic", len(p))
	}
	seen := map[string]bool{}
	for i, s := range p {
		if s.Sequence != i || s.Repeat < 0 || s.Repeat >= 5 || s.Order != i%9 {
			t.Fatalf("bad position: %+v", s)
		}
		if err := validateDiagnosticRequest(s.Stage, s.Mode, 32); err != nil {
			t.Fatal(err)
		}
		key, err := json.Marshal(struct {
			ID, Stage, Mode string
			Repeat          int
		}{s.ID, s.Stage, s.Mode, s.Repeat})
		if err != nil || seen[string(key)] {
			t.Fatalf("duplicate step: %+v", s)
		}
		seen[string(key)] = true
		wantCase := diagnosticCases[i/(5*3*9)]
		if s.DiagnosticCase != wantCase {
			t.Fatalf("case order mismatch: %+v", s)
		}
	}
	firstModes, secondModes := make([]string, 9), make([]string, 9)
	for i := 0; i < 9; i++ {
		firstModes[i], secondModes[i] = p[i].Mode, p[i+9].Mode
	}
	if reflect.DeepEqual(firstModes, secondModes) {
		t.Fatal("mode order never changes")
	}
}

func TestDiagnosticReferenceRestorationAndAlternatingResetIdentity(t *testing.T) {
	retained := NewEncoder()
	for _, q := range []int{1, 3, 1, 3} {
		b := tinyDiagnosticBundle(t, q)
		f, err := prepareDiagnosticFixture(b)
		if err != nil {
			t.Fatal(err)
		}
		if len(f.Frames) != 9 || len(f.Restored) != 9 {
			t.Fatal("missing reference modes")
		}
		for _, mode := range studyModes {
			if !equalBundle(f.Restored[mode], b) || !verify(f.Restored[mode]) {
				t.Fatalf("restoration: %s", mode)
			}
			w, err := retained.Encode(b, mode)
			if err != nil || !bytes.Equal(w, f.Frames[mode]) {
				t.Fatalf("alternating encode: %s: %v", mode, err)
			}
			if strings.HasPrefix(mode, "reset-") && !bytes.Equal(w, f.Frames[strings.TrimPrefix(mode, "reset-")]) {
				t.Fatalf("fresh/reset frame: %s", mode)
			}
		}
	}
	for _, b := range []Bundle{{}, {Root: make([]byte, 32)}} {
		if _, err := prepareDiagnosticFixture(b); err == nil {
			t.Fatal("accepted empty bundle")
		}
	}
	bad := tinyDiagnosticBundle(t, 1)
	bad.Root[0] ^= 1
	if _, err := prepareDiagnosticFixture(bad); err == nil {
		t.Fatal("accepted invalid native proof")
	}
}

func writeDiagnosticTestInput(t *testing.T, dir string, c DiagnosticCase, data []byte) {
	t.Helper()
	p := filepath.Join(dir, c.ID)
	if err := os.MkdirAll(p, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(p, "bundle.json"), data, 0644); err != nil {
		t.Fatal(err)
	}
}

func TestDiagnosticInputValidation(t *testing.T) {
	c := diagnosticCases[0]
	b := tinyDiagnosticBundle(t, c.Q)
	good, err := json.Marshal(b)
	if err != nil {
		t.Fatal(err)
	}
	dir := t.TempDir()
	if _, err := loadDiagnosticBundle(dir, c); err == nil {
		t.Fatal("accepted missing input")
	}
	writeDiagnosticTestInput(t, dir, c, good)
	got, err := loadDiagnosticBundle(dir, c)
	if err != nil || !equalBundle(got, b) {
		t.Fatalf("valid input: %v", err)
	}
	for _, data := range [][]byte{[]byte("{"), []byte("null"), []byte("{}"), append(append([]byte{}, good...), []byte("\n{}")...), bytes.Replace(good, []byte("\"Root\""), []byte("\"unknown\""), 1)} {
		writeDiagnosticTestInput(t, dir, c, data)
		if _, err := loadDiagnosticBundle(dir, c); err == nil {
			t.Fatalf("accepted malformed input: %s", data)
		}
	}
	for _, change := range []func(*Bundle){
		func(b *Bundle) { b.Root[0] ^= 1 },
		func(b *Bundle) { b.Items = append(b.Items, b.Items[0]) },
		func(b *Bundle) { b.Items[0].Value = []byte("short") },
		func(b *Bundle) { b.Items[0].Key = nil },
	} {
		bad := tinyDiagnosticBundle(t, 1)
		change(&bad)
		data, err := json.Marshal(bad)
		if err != nil {
			t.Fatal(err)
		}
		writeDiagnosticTestInput(t, dir, c, data)
		if _, err := loadDiagnosticBundle(dir, c); err == nil {
			t.Fatal("accepted incorrect input shape/proof")
		}
	}
}

func TestDiagnosticThreeStageOutputsAndDeltaFormat(t *testing.T) {
	b := tinyDiagnosticBundle(t, 3)
	f, err := prepareDiagnosticFixture(b)
	if err != nil {
		t.Fatal(err)
	}
	for _, stage := range []string{"encode", "decode", "verify"} {
		for _, mode := range studyModes {
			t.Run(stage+"/"+mode, func(t *testing.T) {
				s := DiagnosticStep{DiagnosticCase: DiagnosticCase{ID: "unit-fixture", Q: 3, Distribution: "unit"}, Stage: stage, Mode: mode}
				row, out, err := measureDiagnosticStage(f, s, 32)
				if err != nil {
					t.Fatal(err)
				}
				if row.DiagnosticStep != s || row.BatchOperations != 32 {
					t.Fatalf("row identity: %+v", row)
				}
				if row.BytesPerOperation != float64(row.AllocatedBytes)/32 || row.MallocsPerOperation != float64(row.Mallocs)/32 {
					t.Fatal("allocation normalization")
				}
				switch stage {
				case "encode":
					if !bytes.Equal(out.Wire, f.Frames[mode]) {
						t.Fatal("encode output mismatch")
					}
				case "decode":
					if !equalBundle(out.Bundle, b) {
						t.Fatal("decode output mismatch")
					}
				case "verify":
					if !out.Verified {
						t.Fatal("verify output false")
					}
				}
				data, err := json.Marshal(row)
				if err != nil {
					t.Fatal(err)
				}
				var obj map[string]any
				if err := json.Unmarshal(data, &obj); err != nil {
					t.Fatal(err)
				}
				for _, key := range []string{"allocated_bytes", "mallocs", "frees", "num_gc", "pause_ns", "bytes_per_operation", "mallocs_per_operation"} {
					v, ok := obj[key].(float64)
					if !ok || v < 0 {
						t.Fatalf("non-numeric/negative delta %s", key)
					}
				}
				for key := range obj {
					if strings.Contains(key, "latency") || strings.Contains(key, "elapsed") {
						t.Fatalf("unexpected timing field %q", key)
					}
				}
			})
		}
	}
}

func TestDiagnosticStageErrorsFail(t *testing.T) {
	for _, stage := range []string{"encode", "decode", "verify"} {
		f, err := prepareDiagnosticFixture(tinyDiagnosticBundle(t, 1))
		if err != nil {
			t.Fatal(err)
		}
		switch stage {
		case "encode":
			f.Bundle.Root = nil
		case "decode":
			f.Frames["ordinary"] = []byte("broken")
		case "verify":
			b := f.Restored["ordinary"]
			b.Root[0] ^= 1
			f.Restored["ordinary"] = b
		}
		if _, _, err := measureDiagnosticStage(f, DiagnosticStep{Stage: stage, Mode: "ordinary"}, 32); err == nil {
			t.Fatalf("swallowed %s failure", stage)
		}
	}
	for _, s := range []DiagnosticStep{{Stage: "bad", Mode: "ordinary"}, {Stage: "encode", Mode: "bad"}} {
		if _, _, err := measureDiagnosticStage(nil, s, 32); err == nil {
			t.Fatal("accepted invalid request")
		}
	}
	if _, _, err := measureDiagnosticStage(nil, DiagnosticStep{Stage: "encode", Mode: "ordinary"}, 1); err == nil {
		t.Fatal("accepted invalid batch")
	}
}

func TestDiagnosticCLIAndExclusiveOutput(t *testing.T) {
	for _, args := range [][]string{nil, {"a"}, {"a", "b", "c"}, {"", "b"}, {"a", ""}} {
		if err := runDiagnostic(args); err == nil {
			t.Fatalf("accepted invalid args %v", args)
		}
	}
	existing := t.TempDir()
	marker := filepath.Join(existing, "marker")
	if err := os.WriteFile(marker, []byte("preserve"), 0644); err != nil {
		t.Fatal(err)
	}
	if err := runDiagnostic([]string{filepath.Join(existing, "missing-input"), existing}); !os.IsExist(err) {
		t.Fatalf("output collision did not fail exclusively: %v", err)
	}
	got, err := os.ReadFile(marker)
	if err != nil || string(got) != "preserve" {
		t.Fatal("existing directory changed")
	}
	out := filepath.Join(t.TempDir(), "new-work")
	if err := runDiagnostic([]string{filepath.Join(t.TempDir(), "missing"), out}); err == nil {
		t.Fatal("accepted missing input directory")
	}
	if _, err := os.Stat(filepath.Join(out, "completion.json")); !os.IsNotExist(err) {
		t.Fatal("failed run emitted completion")
	}
}

// This exercises persistence using only artificial three-leaf native fixtures.
// It neither loads study inputs nor provides diagnostic/performance evidence.
func TestDiagnosticTinyFixtureCLIReceipt(t *testing.T) {
	t.Setenv("GODEBUG", "")
	oldProcs := runtime.GOMAXPROCS(8)
	defer runtime.GOMAXPROCS(oldProcs)
	input := t.TempDir()
	inputBytes := map[string][]byte{}
	for _, c := range diagnosticCases {
		data, err := json.Marshal(tinyDiagnosticBundle(t, c.Q))
		if err != nil {
			t.Fatal(err)
		}
		writeDiagnosticTestInput(t, input, c, data)
		inputBytes[c.ID] = data
	}
	work := filepath.Join(t.TempDir(), "unit-work")
	gogc, gogcSet := os.LookupEnv("GOGC")
	if err := runDiagnostic([]string{input, work}); err != nil {
		t.Fatal(err)
	}
	if after, afterSet := os.LookupEnv("GOGC"); after != gogc || afterSet != gogcSet {
		t.Fatal("GOGC was changed")
	}
	var environment struct {
		ExpectedRows       int              `json:"expected_rows"`
		ExpectedOperations int              `json:"expected_operations"`
		BatchOperations    int              `json:"batch_operations"`
		ExecutionOrder     []DiagnosticStep `json:"execution_order"`
		GoMaxProcs         int              `json:"gomaxprocs"`
		GoDebugEnv         string           `json:"godebug_env"`
		GoDebugEnvSet      bool             `json:"godebug_env_set"`
	}
	data, err := os.ReadFile(filepath.Join(work, "env.json"))
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(data, &environment); err != nil {
		t.Fatal(err)
	}
	if environment.ExpectedRows != 540 || environment.ExpectedOperations != 17280 || environment.BatchOperations != 32 || environment.GoMaxProcs != 8 || !reflect.DeepEqual(environment.ExecutionOrder, diagnosticPlan()) {
		t.Fatal("environment receipt did not retain the exact execution plan")
	}
	if !environment.GoDebugEnvSet || environment.GoDebugEnv != "" {
		t.Fatal("environment receipt lost GODEBUG value/presence")
	}
	log, err := os.Open(filepath.Join(work, "log.jsonl"))
	if err != nil {
		t.Fatal(err)
	}
	defer log.Close()
	scanner := bufio.NewScanner(log)
	rows, operations := 0, 0
	for scanner.Scan() {
		var row DiagnosticRow
		if err := json.Unmarshal(scanner.Bytes(), &row); err != nil {
			t.Fatal(err)
		}
		if rows >= len(environment.ExecutionOrder) || row.DiagnosticStep != environment.ExecutionOrder[rows] || row.BatchOperations != 32 {
			t.Fatalf("row %d disagrees with plan", rows)
		}
		rows++
		operations += row.BatchOperations
	}
	if err := scanner.Err(); err != nil {
		t.Fatal(err)
	}
	var completion struct {
		Complete           bool `json:"complete"`
		Rows               int  `json:"rows"`
		ExpectedRows       int  `json:"expected_rows"`
		Operations         int  `json:"operations"`
		ExpectedOperations int  `json:"expected_operations"`
	}
	data, err = os.ReadFile(filepath.Join(work, "completion.json"))
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(data, &completion); err != nil {
		t.Fatal(err)
	}
	if rows != 540 || operations != 17280 || !completion.Complete || completion.Rows != rows || completion.ExpectedRows != rows || completion.Operations != operations || completion.ExpectedOperations != operations {
		t.Fatal("incomplete or inconsistent run receipt")
	}
	for _, c := range diagnosticCases {
		data, err := os.ReadFile(filepath.Join(input, c.ID, "bundle.json"))
		if err != nil || !bytes.Equal(data, inputBytes[c.ID]) {
			t.Fatalf("input %s was changed: %v", c.ID, err)
		}
	}
}
