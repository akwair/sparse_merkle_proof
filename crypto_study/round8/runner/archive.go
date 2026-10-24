package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strings"
)

type checkpoint struct {
	Domain             string `json:"domain"`
	N                  int    `json:"n"`
	ValueBytes         int    `json:"value_bytes"`
	Root               []byte `json:"root"`
	Keys, Values       [][]byte
	MemberPrefixCounts [16]int `json:"member_prefix_counts"`
}
type requestSet struct {
	Domain       string `json:"domain"`
	N            int    `json:"n"`
	Distribution string `json:"distribution"`
	Batch        int    `json:"batch"`
	ID           string `json:"request_set_id"`
	Indexes      []int  `json:"request_indexes"`
}
type requestMetadata struct {
	Domain       string `json:"domain"`
	N            int    `json:"n"`
	Q            int    `json:"q"`
	ValueBytes   int    `json:"value_bytes"`
	Distribution string `json:"distribution"`
	Batch        int    `json:"batch"`
	ID           string `json:"id"`
	Cell         string `json:"cell"`
	Kind         string `json:"kind"`
	Pattern      string `json:"pattern"`
	RequestSetID string `json:"request_set_id"`
	Indexes      []int  `json:"request_indexes"`
}
type archiveCase struct {
	treeID     string
	batches    map[int][]int
	references map[int]map[string][]byte
}
type Archive struct {
	trees  map[string]*FrozenTree
	cases  map[string]*archiveCase
	Hashes map[string]string
	root   string
}

func strictJSON(raw []byte, out any) error {
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if e := d.Decode(out); e != nil {
		return e
	}
	if e := d.Decode(new(any)); e != io.EOF {
		return fmt.Errorf("JSON trailing value or invalid suffix: %v", e)
	}
	return nil
}
func readArtifact(path string, limit int64, hashes map[string]string) ([]byte, error) {
	info, e := os.Lstat(path)
	if e != nil {
		return nil, e
	}
	if !info.Mode().IsRegular() || info.Size() > limit {
		return nil, fmt.Errorf("not regular or oversized artifact %s", path)
	}
	f, e := os.Open(path)
	if e != nil {
		return nil, e
	}
	defer f.Close()
	raw, e := io.ReadAll(io.LimitReader(f, limit+1))
	if e != nil {
		return nil, e
	}
	if int64(len(raw)) > limit {
		return nil, fmt.Errorf("artifact over limit")
	}
	s := sha256.Sum256(raw)
	hashes[path] = hex.EncodeToString(s[:])
	return raw, nil
}
func readJSONArtifact(path string, limit int64, out any, hashes map[string]string) error {
	raw, e := readArtifact(path, limit, hashes)
	if e != nil {
		return e
	}
	if e = strictJSON(raw, out); e != nil {
		return fmt.Errorf("%s: %w", path, e)
	}
	return nil
}
func validMode(mode string) bool {
	for _, m := range studyModes {
		if mode == m {
			return true
		}
	}
	return false
}

// LoadArchive consumes recorded inputs only; it never regenerates keys, values or requests.
// A selected case loads its three batches. An empty selection loads all 16 primary cases.
func LoadArchive(root string, selected []string) (*Archive, error) {
	return loadArchive(root, selected, true)
}

// Client loading validates archived bindings and frames without rebuilding SMT maps.
func LoadClientArchive(root string, selected []string) (*Archive, error) {
	return loadArchive(root, selected, false)
}
func loadArchive(root string, selected []string, rebuild bool) (*Archive, error) {
	abs, e := filepath.Abs(root)
	if e != nil {
		return nil, e
	}
	a := &Archive{root: abs, trees: map[string]*FrozenTree{}, cases: map[string]*archiveCase{}, Hashes: map[string]string{}}
	var sets []requestSet
	if e = readJSONArtifact(filepath.Join(abs, "request_sets.json"), 1<<20, &sets, a.Hashes); e != nil {
		return nil, e
	}
	setMap := map[string]requestSet{}
	for _, s := range sets {
		expected := fmt.Sprintf("%s_n%d_%s_b%d", s.Domain, s.N, s.Distribution, s.Batch)
		if (s.Domain != "dev" && s.Domain != "confirm") || (s.N != 4096 && s.N != 16384) || (s.Distribution != "uniform" && s.Distribution != "zipf") || s.Batch < 0 || s.Batch > 2 || s.ID != expected || len(s.Indexes) != 128 {
			return nil, fmt.Errorf("invalid request set %s", s.ID)
		}
		if _, ok := setMap[s.ID]; ok {
			return nil, fmt.Errorf("duplicate request set")
		}
		for _, idx := range s.Indexes {
			if idx < 0 || idx >= s.N {
				return nil, fmt.Errorf("request index out of bounds")
			}
		}
		setMap[s.ID] = s
	}
	if len(sets) != 24 {
		return nil, fmt.Errorf("expected 24 request sets")
	}
	wanted := map[string]bool{}
	for _, id := range selected {
		wanted[id] = true
	}
	for _, domain := range []string{"dev", "confirm"} {
		for _, n := range []int{4096, 16384} {
			for _, v := range []int{32, 1000} {
				for _, q := range []int{1, 128} {
					for _, dist := range []string{"uniform", "zipf"} {
						cell := fmt.Sprintf("n%d_q%d_v%d_member_%s", n, q, v, dist)
						id := domain + "_" + cell
						if len(selected) > 0 && !wanted[id] {
							continue
						}
						if len(selected) == 0 && n != 16384 {
							continue
						}
						treeID := fmt.Sprintf("%s_n%d_v%d", domain, n, v)
						ft := a.trees[treeID]
						if ft == nil {
							var cp checkpoint
							if e = readJSONArtifact(filepath.Join(abs, "tree_"+treeID+".json"), 32<<20, &cp, a.Hashes); e != nil {
								return nil, e
							}
							if cp.Domain != domain || cp.N != n || cp.ValueBytes != v {
								return nil, fmt.Errorf("checkpoint metadata mismatch")
							}
							if rebuild {
								ft, e = freezeCheckpoint(cp, true)
							} else {
								ft, e = trustedCheckpoint(cp)
							}
							if e != nil {
								return nil, e
							}
							a.trees[treeID] = ft
						}
						c := &archiveCase{treeID: treeID, batches: map[int][]int{}, references: map[int]map[string][]byte{}}
						a.cases[id] = c
						for batch := 0; batch < 3; batch++ {
							dir := filepath.Join(abs, fmt.Sprintf("%s_b%d", id, batch))
							var meta requestMetadata
							if e = readJSONArtifact(filepath.Join(dir, "requests.json"), 1<<20, &meta, a.Hashes); e != nil {
								return nil, e
							}
							setID := fmt.Sprintf("%s_n%d_%s_b%d", domain, n, dist, batch)
							set, ok := setMap[setID]
							if !ok || meta.Domain != domain || meta.N != n || meta.Q != q || meta.ValueBytes != v || meta.Distribution != dist || meta.Pattern != dist || meta.Batch != batch || meta.ID != fmt.Sprintf("%s_b%d", id, batch) || meta.Cell != cell || meta.Kind != "member" || meta.RequestSetID != setID || !reflect.DeepEqual(meta.Indexes, set.Indexes[:q]) {
								return nil, fmt.Errorf("request metadata/vector mismatch %s", dir)
							}
							c.batches[batch] = append([]int(nil), meta.Indexes...)
							var b Bundle
							if e = readJSONArtifact(filepath.Join(dir, "bundle.json"), maxWire, &b, a.Hashes); e != nil {
								return nil, e
							}
							if !a.Accept(id, batch, b) {
								return nil, fmt.Errorf("archived bundle binding failed %s", dir)
							}
							c.references[batch] = map[string][]byte{}
							for _, mode := range studyModes {
								if strings.HasPrefix(mode, "reset-") {
									continue
								}
								raw, e := readArtifact(filepath.Join(dir, mode+".wire"), maxWire, a.Hashes)
								if e != nil {
									return nil, e
								}
								restored, e := decodeStudy(raw, mode)
								if e != nil || !a.Accept(id, batch, restored) || !equalBundle(b, restored) {
									return nil, fmt.Errorf("reference restoration failed %s/%s", dir, mode)
								}
								c.references[batch][mode] = raw
							}
						}
						delete(wanted, id)
					}
				}
			}
		}
	}
	if len(wanted) != 0 || len(a.cases) == 0 {
		return nil, fmt.Errorf("unknown or empty selected case set")
	}
	// Verify the worker pipeline against all nine archived mode oracles before publication.
	if rebuild {
		if _, e = a.Check(); e != nil {
			return nil, e
		}
	}
	return a, nil
}
func (a *Archive) RequestKeys(id string, batch int) ([][]byte, error) {
	c, ok := a.cases[id]
	if !ok {
		return nil, fmt.Errorf("unknown case")
	}
	idxs, ok := c.batches[batch]
	if !ok {
		return nil, fmt.Errorf("invalid batch")
	}
	ft := a.trees[c.treeID]
	out := make([][]byte, len(idxs))
	for i, idx := range idxs {
		out[i] = append([]byte(nil), ft.keys[idx]...)
	}
	return out, nil
}
func (a *Archive) Accept(id string, batch int, b Bundle) bool {
	c, ok := a.cases[id]
	if !ok {
		return false
	}
	idxs, ok := c.batches[batch]
	if !ok {
		return false
	}
	ft := a.trees[c.treeID]
	if !bytes.Equal(ft.root, b.Root) || len(b.Items) != len(idxs) {
		return false
	}
	for i, idx := range idxs {
		if !bytes.Equal(b.Items[i].Key, ft.keys[idx]) || !bytes.Equal(b.Items[i].Value, ft.checkpointValues[idx]) {
			return false
		}
	}
	return verify(b)
}

// FrameMatches is a post-latency preservation gate; it never serves proof observations.
func (a *Archive) FrameMatches(id string, batch int, mode string, raw []byte) bool {
	c, ok := a.cases[id]
	if !ok || !validMode(mode) {
		return false
	}
	ref, ok := c.references[batch][strings.TrimPrefix(mode, "reset-")]
	return ok && bytes.Equal(raw, ref)
}
func (a *Archive) Check() (map[string]any, error) {
	w, e := a.NewWorker()
	if e != nil {
		return nil, e
	}
	frames := 0
	ids := make([]string, 0, len(a.cases))
	for id := range a.cases {
		ids = append(ids, id)
	}
	sort.Strings(ids)
	for _, id := range ids {
		c := a.cases[id]
		for batch := 0; batch < 3; batch++ {
			for _, mode := range studyModes {
				raw, _, e := w.Serve(id, batch, mode)
				if e != nil {
					return nil, e
				}
				b, e := decodeStudy(raw, mode)
				if e != nil || !a.Accept(id, batch, b) {
					return nil, fmt.Errorf("native restoration failed %s %d %s", id, batch, mode)
				}
				if c.references != nil {
					ref := c.references[batch][strings.TrimPrefix(mode, "reset-")]
					if !bytes.Equal(raw, ref) {
						return nil, fmt.Errorf("frame mismatch %s %d %s", id, batch, mode)
					}
				}
				frames++
			}
		}
	}
	return map[string]any{"complete": true, "cases": len(a.cases), "trees": len(a.trees), "batches": 3, "modes": len(studyModes), "frames_checked": frames, "data_hashes": a.Hashes}, nil
}
