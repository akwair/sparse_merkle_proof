package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io/fs"
	"math/rand"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TestCrossPlatformFullCorpus reconstructs the complete preregistered corpus
// without invoking main or taking timestamps. Expected hashes come from the
// frozen Round4 artifacts, not from another invocation of the current encoder.
func TestCrossPlatformFullCorpus(t *testing.T) {
	manifestBytes, err := os.ReadFile(filepath.FromSlash("../prior/round4_fixture_hashes.json"))
	if err != nil {
		t.Fatal(err)
	}
	var expected struct {
		Files                     map[string]string `json:"files"`
		ObservationIdentitySHA256 string            `json:"observation_identity_sha256"`
		ObservationCount          int               `json:"observation_count"`
	}
	if err := json.Unmarshal(manifestBytes, &expected); err != nil {
		t.Fatal(err)
	}
	if len(expected.Files) != 1542 || expected.ObservationCount != 36288 {
		t.Fatalf("incomplete Round4 manifest: files=%d observations=%d", len(expected.Files), expected.ObservationCount)
	}
	if digest, err := hex.DecodeString(expected.ObservationIdentitySHA256); err != nil || len(digest) != sha256.Size {
		t.Fatal("invalid observation identity SHA256")
	}

	work := t.TempDir()
	var ws []Workload
	for _, domain := range []string{"dev", "confirm"} {
		for _, n := range []int{4096, 16384} {
			items, checkpoint, err := MakeWorkloads(domain, n)
			if err != nil {
				t.Fatalf("MakeWorkloads(%s,%d): %v", domain, n, err)
			}
			if len(items) != 48 {
				t.Fatalf("%s N=%d: got %d bundles, want 48", domain, n, len(items))
			}
			ws = append(ws, items...)
			save(filepath.Join(work, fmt.Sprintf("tree_%s_n%d.json", domain, n)), checkpoint)
			t.Logf("reconstructed %s N=%d: 48 bundles", domain, n)
		}
	}
	if len(ws) != 192 || len(studyModes) != 9 {
		t.Fatalf("matrix changed: bundles=%d modes=%d", len(ws), len(studyModes))
	}
	rng := rand.New(rand.NewSource(3407))
	rng.Shuffle(len(ws), func(i, j int) { ws[i], ws[j] = ws[j], ws[i] })
	orderIDs := []string{}
	for _, w := range ws {
		orderIDs = append(orderIDs, w.ID)
	}
	save(filepath.Join(work, "execution_order.json"), orderIDs)
	modeRng := rng
	identity := sha256.New()
	observations, restorations, frames := 0, 0, 0
	var diagnostics []map[string]interface{}
	for _, w := range ws {
		dir := filepath.Join(work, w.ID)
		if err := os.Mkdir(dir, 0755); err != nil {
			t.Fatal(err)
		}
		save(filepath.Join(dir, "bundle.json"), w.Bundle)
		wires := map[string][]byte{}
		sizes := map[string]int{}
		reference := NewEncoder()
		for _, mode := range studyModes {
			raw, err := reference.Encode(w.Bundle, mode)
			if err != nil {
				t.Fatalf("encode %s/%s: %v", w.ID, mode, err)
			}
			decoded, err := decodeStudy(raw, mode)
			if err != nil || !equalBundle(w.Bundle, decoded) || !verify(decoded) {
				t.Fatalf("restore/verify %s/%s: %v", w.ID, mode, err)
			}
			restorations++
			wires[mode] = raw
			sizes[mode] = len(raw)
			if strings.HasPrefix(mode, "reset-") {
				if !bytes.Equal(raw, wires[strings.TrimPrefix(mode, "reset-")]) {
					t.Fatalf("reset/fresh bytes differ: %s/%s", w.ID, mode)
				}
			} else {
				frame(filepath.Join(dir, mode+".wire"), raw)
				frames++
			}
		}
		diag := structure(w, sizes)
		diagnostics = append(diagnostics, diag)
		save(filepath.Join(dir, "diagnostics.json"), diag)
		// Advance the same generator after the initial shuffle. Hash only the
		// fixed observation identities; no measurements or warmups are run.
		for rep := 0; rep < 21; rep++ {
			for order, mi := range modeRng.Perm(len(studyModes)) {
				mode := studyModes[mi]
				fmt.Fprintf(identity, "%s\t%d\t%d\t%s\t%d\n", w.ID, rep, order, mode, sizes[mode])
				observations++
			}
		}
	}
	save(filepath.Join(work, "diagnostics.json"), diagnostics)
	if observations != 36288 || restorations != 1728 || frames != 1152 || len(diagnostics) != 192 {
		t.Fatalf("corpus counts: observations=%d restorations=%d frames=%d diagnostics=%d", observations, restorations, frames, len(diagnostics))
	}
	if got := hex.EncodeToString(identity.Sum(nil)); got != expected.ObservationIdentitySHA256 {
		t.Fatalf("observation identity SHA256=%s, want %s", got, expected.ObservationIdentitySHA256)
	}
	checked := 0
	err = filepath.WalkDir(work, func(path string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if entry.IsDir() {
			return nil
		}
		rel, err := filepath.Rel(work, path)
		if err != nil {
			return err
		}
		rel = filepath.ToSlash(rel)
		want, found := expected.Files[rel]
		if !found {
			return fmt.Errorf("unexpected generated artifact: %s", rel)
		}
		raw, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		if got := fmt.Sprintf("%x", sha256.Sum256(raw)); got != want {
			return fmt.Errorf("artifact %s SHA256=%s, want %s", rel, got, want)
		}
		checked++
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	if checked != 1542 {
		t.Fatalf("checked %d generated files, want 1542", checked)
	}
	t.Logf("matched all %d artifact hashes; restored/verified %d bundle-mode pairs; matched %d observation identities (SHA256 %s)", checked, restorations, observations, expected.ObservationIdentitySHA256)
}
