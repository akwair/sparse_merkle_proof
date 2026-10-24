package main

import (
	"bytes"
	"crypto/sha256"
	"fmt"
	smt "github.com/celestiaorg/smt"
	stdhash "hash"
	"time"
)

type startupStore struct{ m map[string][]byte }

func (s *startupStore) Get(k []byte) ([]byte, error) {
	if v, ok := s.m[string(k)]; ok {
		return v, nil
	}
	return nil, &smt.InvalidKeyError{Key: append([]byte(nil), k...)}
}
func (s *startupStore) Set(k, v []byte) error { s.m[string(k)] = append([]byte(nil), v...); return nil }
func (s *startupStore) Delete(k []byte) error {
	if _, ok := s.m[string(k)]; !ok {
		return &smt.InvalidKeyError{Key: append([]byte(nil), k...)}
	}
	delete(s.m, string(k))
	return nil
}

type frozenMapStore struct{ m map[string][]byte }

func (s *frozenMapStore) Get(k []byte) ([]byte, error) {
	if v, ok := s.m[string(k)]; ok {
		return v, nil
	}
	return nil, &smt.InvalidKeyError{Key: append([]byte(nil), k...)}
}
func (s *frozenMapStore) Set(k, v []byte) error { return fmt.Errorf("frozen map is read-only") }
func (s *frozenMapStore) Delete(k []byte) error { return fmt.Errorf("frozen map is read-only") }

type FrozenTree struct {
	nodes, values          *frozenMapStore
	keys, checkpointValues [][]byte
	root                   []byte
}

func trustedCheckpoint(cp checkpoint) (*FrozenTree, error) {
	if cp.N < 1 || len(cp.Root) != 32 || len(cp.Keys) != cp.N || len(cp.Values) != cp.N || (cp.ValueBytes != 32 && cp.ValueBytes != 1000) {
		return nil, fmt.Errorf("checkpoint shape")
	}
	ft := &FrozenTree{root: append([]byte(nil), cp.Root...)}
	seen := map[string]bool{}
	for i, k := range cp.Keys {
		if len(k) != 32 || len(cp.Values[i]) != cp.ValueBytes || seen[string(k)] {
			return nil, fmt.Errorf("checkpoint key/value shape or duplicate")
		}
		seen[string(k)] = true
		ft.keys = append(ft.keys, append([]byte(nil), k...))
		ft.checkpointValues = append(ft.checkpointValues, append([]byte(nil), cp.Values[i]...))
	}
	return ft, nil
}
func freezeCheckpoint(cp checkpoint, requireRoot bool) (*FrozenTree, error) {
	if cp.N < 1 || len(cp.Keys) != cp.N || len(cp.Values) != cp.N || (cp.ValueBytes != 32 && cp.ValueBytes != 1000) || requireRoot && len(cp.Root) != 32 {
		return nil, fmt.Errorf("checkpoint shape")
	}
	ns := &startupStore{m: map[string][]byte{}}
	vs := &startupStore{m: map[string][]byte{}}
	tree := smt.NewSparseMerkleTree(ns, vs, sha256.New())
	ft := &FrozenTree{}
	seen := map[string]bool{}
	for i, k := range cp.Keys {
		if len(k) != 32 || len(cp.Values[i]) != cp.ValueBytes || seen[string(k)] {
			return nil, fmt.Errorf("checkpoint key/value shape or duplicate")
		}
		seen[string(k)] = true
		key := append([]byte(nil), k...)
		value := append([]byte(nil), cp.Values[i]...)
		if _, e := tree.Update(key, value); e != nil {
			return nil, e
		}
		ft.keys = append(ft.keys, key)
		ft.checkpointValues = append(ft.checkpointValues, value)
	}
	ft.root = append([]byte(nil), tree.Root()...)
	if requireRoot && !bytes.Equal(ft.root, cp.Root) {
		return nil, fmt.Errorf("rebuilt root mismatch")
	}
	ft.nodes = &frozenMapStore{m: ns.m}
	ft.values = &frozenMapStore{m: vs.m}
	ns.m = nil
	vs.m = nil
	return ft, nil
}

type treeReader interface {
	Get([]byte) ([]byte, error)
	Prove([]byte) (smt.SparseMerkleProof, error)
}
type Worker struct {
	archive *Archive
	trees   map[string]treeReader
	encoder *Encoder
	hashers []stdhash.Hash
}
type ServerStages struct {
	QueueNS  int64 `json:"queue_ns"`
	ProofNS  int64 `json:"proof_ns"`
	EncodeNS int64 `json:"encode_ns"`
}

func (a *Archive) NewWorker() (*Worker, error) { return a.newWorkerWithHash(sha256.New) }
func (a *Archive) newWorkerWithHash(factory func() stdhash.Hash) (*Worker, error) {
	w := &Worker{archive: a, trees: map[string]treeReader{}, encoder: NewEncoder()}
	for id, ft := range a.trees {
		h := factory()
		w.hashers = append(w.hashers, h)
		w.trees[id] = smt.ImportSparseMerkleTree(ft.nodes, ft.values, h, append([]byte(nil), ft.root...))
	}
	return w, nil
}
func (w *Worker) Serve(id string, batch int, mode string) ([]byte, ServerStages, error) {
	keys, e := w.archive.RequestKeys(id, batch)
	if e != nil {
		return nil, ServerStages{}, e
	}
	return w.serveKeys(id, batch, mode, keys)
}
func (w *Worker) serveKeys(id string, batch int, mode string, keys [][]byte) ([]byte, ServerStages, error) {
	var st ServerStages
	c, ok := w.archive.cases[id]
	if !ok || !validMode(mode) {
		return nil, st, fmt.Errorf("invalid case/mode")
	}
	idxs, ok := c.batches[batch]
	if !ok || len(keys) != len(idxs) {
		return nil, st, fmt.Errorf("invalid batch/keys")
	}
	ft := w.archive.trees[c.treeID]
	for i, k := range keys {
		if !bytes.Equal(k, ft.keys[idxs[i]]) {
			return nil, st, fmt.Errorf("request key binding")
		}
	}
	tree := w.trees[c.treeID]
	t0 := time.Now()
	b := Bundle{Root: append([]byte(nil), ft.root...)}
	for _, k := range keys {
		v, e := tree.Get(k)
		if e != nil {
			return nil, st, e
		}
		p, e := tree.Prove(k)
		if e != nil {
			return nil, st, e
		}
		b.Items = append(b.Items, Item{Key: append([]byte(nil), k...), Value: append([]byte(nil), v...), Proof: p})
	}
	t1 := time.Now()
	raw, e := w.encoder.Encode(b, mode)
	t2 := time.Now()
	st.ProofNS = t1.Sub(t0).Nanoseconds()
	st.EncodeNS = t2.Sub(t1).Nanoseconds()
	return raw, st, e
}
