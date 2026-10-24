package main

import (
	"bytes"
	"compress/zlib"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"fmt"
	smt "github.com/celestiaorg/smt"
	"io"
	"math/rand"
	"os"
	"path/filepath"
	"runtime"
	"time"
)

type Item struct {
	Key, Value []byte
	Proof      smt.SparseMerkleProof
}
type Bundle struct {
	Root  []byte
	Items []Item
}

var modes = []string{"ordinary", "compact", "zlib-ordinary", "zlib-compact"}

const maxWire = 8 * 1024 * 1024

func modeIndex(m string) (int, error) {
	for i, x := range modes {
		if x == m {
			return i, nil
		}
	}
	return 0, fmt.Errorf("mode")
}
func compactMode(m string) bool { return m == "compact" || m == "zlib-compact" }
func put16(w *bytes.Buffer, n int) {
	if n < 0 || n > 65535 {
		panic("uint16")
	}
	binary.Write(w, binary.BigEndian, uint16(n))
}
func blob(w *bytes.Buffer, v []byte) { put16(w, len(v)); w.Write(v) }
func encode(b Bundle, m string) ([]byte, error) {
	idx, e := modeIndex(m)
	if e != nil {
		return nil, e
	}
	if len(b.Root) != 32 || len(b.Items) < 1 || len(b.Items) > 256 {
		return nil, fmt.Errorf("bundle shape")
	}
	var out bytes.Buffer
	out.Write(b.Root)
	put16(&out, len(b.Items))
	for _, it := range b.Items {
		if len(it.Key) > 4096 || len(it.Value) > 4096 {
			return nil, fmt.Errorf("field limit")
		}
		blob(&out, it.Key)
		blob(&out, it.Value)
		p := it.Proof
		nodes := p.SideNodes
		if compactMode(m) {
			c, e := smt.CompactProof(p, sha256.New())
			if e != nil {
				return nil, e
			}
			put16(&out, c.NumSideNodes)
			out.Write(c.BitMask)
			nodes = c.SideNodes
		}
		if len(nodes) > 256 {
			return nil, fmt.Errorf("depth")
		}
		put16(&out, len(nodes))
		for _, v := range nodes {
			if len(v) != 32 {
				return nil, fmt.Errorf("node size")
			}
			out.Write(v)
		}
		blob(&out, p.NonMembershipLeafData)
		blob(&out, p.SiblingData)
	}
	raw := out.Bytes()
	if idx >= 2 {
		var z bytes.Buffer
		w, e := zlib.NewWriterLevel(&z, 6)
		if e != nil {
			return nil, e
		}
		if _, e = w.Write(raw); e != nil {
			return nil, e
		}
		if e = w.Close(); e != nil {
			return nil, e
		}
		raw = z.Bytes()
	}
	return append([]byte{'E', '3', byte(idx), 0}, raw...), nil
}

type reader struct {
	b []byte
	p int
}

func (r *reader) take(n int) ([]byte, error) {
	if n < 0 || r.p+n > len(r.b) {
		return nil, io.ErrUnexpectedEOF
	}
	v := r.b[r.p : r.p+n]
	r.p += n
	return v, nil
}
func (r *reader) n16() (int, error) {
	v, e := r.take(2)
	if e != nil {
		return 0, e
	}
	return int(binary.BigEndian.Uint16(v)), nil
}
func (r *reader) blob(limit int) ([]byte, error) {
	n, e := r.n16()
	if e != nil {
		return nil, e
	}
	if n > limit {
		return nil, fmt.Errorf("field limit")
	}
	if n == 0 {
		return nil, nil
	}
	return r.take(n)
}
func decode(w []byte, m string) (Bundle, error) {
	var b Bundle
	idx, e := modeIndex(m)
	if e != nil {
		return b, e
	}
	if len(w) > maxWire || len(w) < 4 || !bytes.Equal(w[:4], []byte{'E', '3', byte(idx), 0}) {
		return b, fmt.Errorf("envelope")
	}
	raw := w[4:]
	if idx >= 2 {
		src := bytes.NewReader(raw)
		z, e := zlib.NewReader(src)
		if e != nil {
			return b, e
		}
		raw, e = io.ReadAll(io.LimitReader(z, maxWire+1))
		ce := z.Close()
		if e != nil || ce != nil || len(raw) > maxWire || src.Len() != 0 {
			return b, fmt.Errorf("inflate/trailing")
		}
	}
	r := reader{b: raw}
	b.Root, e = r.take(32)
	if e != nil {
		return b, e
	}
	n, e := r.n16()
	if e != nil || n < 1 || n > 256 {
		return b, fmt.Errorf("count")
	}
	for i := 0; i < n; i++ {
		var it Item
		it.Key, e = r.blob(4096)
		if e != nil {
			return b, e
		}
		it.Value, e = r.blob(4096)
		if e != nil {
			return b, e
		}
		depth := 0
		var mask []byte
		if compactMode(m) {
			depth, e = r.n16()
			if e != nil || depth > 256 {
				return b, fmt.Errorf("depth")
			}
			mask, e = r.take((depth + 7) / 8)
			if e != nil {
				return b, e
			}
		}
		k, e := r.n16()
		if e != nil || k > 256 {
			return b, fmt.Errorf("nodes")
		}
		var nodes [][]byte
		for j := 0; j < k; j++ {
			v, e := r.take(32)
			if e != nil {
				return b, e
			}
			nodes = append(nodes, v)
		}
		nm, e := r.blob(65)
		if e != nil {
			return b, e
		}
		sd, e := r.blob(65)
		if e != nil {
			return b, e
		}
		it.Proof = smt.SparseMerkleProof{SideNodes: nodes, NonMembershipLeafData: nm, SiblingData: sd}
		if compactMode(m) {
			it.Proof, e = smt.DecompactProof(smt.SparseCompactMerkleProof{SideNodes: nodes, NonMembershipLeafData: nm, SiblingData: sd, BitMask: mask, NumSideNodes: depth}, sha256.New())
			if e != nil {
				return b, e
			}
		}
		b.Items = append(b.Items, it)
	}
	if r.p != len(raw) {
		return b, fmt.Errorf("trailing")
	}
	return b, nil
}
func equalBundle(a, b Bundle) bool {
	// nil and empty slices have the same documented proof meaning.
	if !bytes.Equal(a.Root, b.Root) || len(a.Items) != len(b.Items) {
		return false
	}
	for i, x := range a.Items {
		y := b.Items[i]
		if !bytes.Equal(x.Key, y.Key) || !bytes.Equal(x.Value, y.Value) || !bytes.Equal(x.Proof.NonMembershipLeafData, y.Proof.NonMembershipLeafData) || !bytes.Equal(x.Proof.SiblingData, y.Proof.SiblingData) || len(x.Proof.SideNodes) != len(y.Proof.SideNodes) {
			return false
		}
		for j, v := range x.Proof.SideNodes {
			if !bytes.Equal(v, y.Proof.SideNodes[j]) {
				return false
			}
		}
	}
	return true
}
func verify(b Bundle) bool {
	for _, it := range b.Items {
		if !smt.VerifyProof(it.Proof, b.Root, it.Key, it.Value, sha256.New()) {
			return false
		}
	}
	return true
}
func must(e error) {
	if e != nil {
		panic(e)
	}
}
func save(p string, v interface{}) {
	f, e := os.OpenFile(p, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
	must(e)
	defer f.Close()
	enc := json.NewEncoder(f)
	enc.SetIndent("", "  ")
	must(enc.Encode(v))
}
func frame(p string, v []byte) {
	f, e := os.OpenFile(p, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
	must(e)
	_, e = f.Write(v)
	must(e)
	must(f.Close())
}
func hash(s string) []byte { x := sha256.Sum256([]byte(s)); return x[:] }
func legacyMain() {
	if len(os.Args) != 2 {
		panic("usage: external_runner workdir")
	}
	work := os.Args[1]
	must(os.Mkdir(work, 0755))
	save(filepath.Join(work, "environment.json"), map[string]interface{}{"clock": "QueryPerformanceCounter", "clock_frequency": timerFrequency, "go": runtime.Version(), "os": runtime.GOOS, "arch": runtime.GOARCH, "cpus": runtime.NumCPU(), "gomaxprocs": runtime.GOMAXPROCS(0), "seed": 3407, "commit": "dba215ccb88452c31d823bf156d8f35406c1dc04"})
	log, e := os.OpenFile(filepath.Join(work, "log.jsonl"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
	must(e)
	defer log.Close()
	enc := json.NewEncoder(log)
	var diags []map[string]interface{}
	rows := 0
	rng := rand.New(rand.NewSource(3407))
	for _, domain := range []string{"dev", "confirm"} {
		for _, n := range []int{128, 512, 2048} {
			tree := smt.NewSparseMerkleTree(smt.NewSimpleMap(), smt.NewSimpleMap(), sha256.New())
			keys := make([][]byte, n)
			values := make([][]byte, n)
			for i := 0; i < n; i++ {
				keys[i] = hash(fmt.Sprintf("r3/%s/3407/key/%d", domain, i))
				values[i] = hash(fmt.Sprintf("r3/%s/3407/value/%d", domain, i))
				_, e = tree.Update(keys[i], values[i])
				must(e)
			}
			for _, q := range []int{1, 32} {
				for _, kind := range []string{"member", "absent"} {
					for bi := 0; bi < 3; bi++ {
						cell := fmt.Sprintf("n%d_q%d_%s", n, q, kind)
						id := fmt.Sprintf("%s_%s_b%d", domain, cell, bi)
						dir := filepath.Join(work, id)
						must(os.Mkdir(dir, 0755))
						b := Bundle{Root: tree.Root()}
						depths := []int{}
						retained := []int{}
						masks := []int{}
						for j := 0; j < q; j++ {
							idx := (bi*q + j) % n
							k, v := keys[idx], values[idx]
							if kind == "absent" {
								k = hash(fmt.Sprintf("r3/%s/3407/absent/%d", domain, bi*q+j))
								v = nil
							}
							p, e := tree.Prove(k)
							must(e)
							c, e := smt.CompactProof(p, sha256.New())
							must(e)
							b.Items = append(b.Items, Item{Key: k, Value: v, Proof: p})
							depths = append(depths, len(p.SideNodes))
							retained = append(retained, len(c.SideNodes))
							masks = append(masks, len(c.BitMask))
						}
						if !verify(b) {
							panic("source proof invalid")
						}
						save(filepath.Join(dir, "bundle.json"), b)
						wires := map[string][]byte{}
						sizes := map[string]int{}
						for _, m := range modes {
							w, e := encode(b, m)
							must(e)
							out, e := decode(w, m)
							must(e)
							if !equalBundle(b, out) || !verify(out) {
								panic("correctness")
							}
							wires[m] = w
							sizes[m] = len(w)
							frame(filepath.Join(dir, m+".wire"), w)
						}
						expected := 0
						for j, d := range depths {
							expected += 32*(d-retained[j]) - 2 - masks[j]
						}
						if sizes["ordinary"]-sizes["compact"] != expected {
							panic("size identity")
						}
						diags = append(diags, map[string]interface{}{"domain": domain, "cell": cell, "batch": bi, "depths": depths, "retained": retained, "masks": masks, "sizes": sizes, "identity_saving": expected})
						for _, m := range modes {
							for w := 0; w < 2; w++ {
								raw, e := encode(b, m)
								must(e)
								out, e := decode(raw, m)
								must(e)
								if !verify(out) {
									panic("warmup")
								}
							}
						}
						for rep := 0; rep < 21; rep++ {
							for order, mi := range rng.Perm(len(modes)) {
								m := modes[mi]
								t0 := timestamp()
								raw, e := encode(b, m)
								t1 := timestamp()
								must(e)
								out, e := decode(raw, m)
								t2 := timestamp()
								must(e)
								ok := verify(out)
								t3 := timestamp()
								runtime.KeepAlive(raw)
								runtime.KeepAlive(out)
								if !ok || !bytes.Equal(raw, wires[m]) || !equalBundle(out, b) {
									panic("timed correctness")
								}
								must(enc.Encode(map[string]interface{}{"host": "external", "domain": domain, "cell": cell, "batch": bi, "repeat": rep, "order": order, "mode": m, "bytes": len(raw), "encode_ns": elapsed(t0, t1), "decode_ns": elapsed(t1, t2), "verify_ns": elapsed(t2, t3), "total_ns": elapsed(t0, t3)}))
								rows++
							}
						}
						fmt.Println("external finished", id)
					}
				}
			}
		}
	}
	save(filepath.Join(work, "diagnostics.json"), diags)
	must(log.Sync())
	save(filepath.Join(work, "completion.json"), map[string]interface{}{"rows": rows, "expected": 6048, "complete": rows == 6048, "utc": time.Now().UTC().Format(time.RFC3339)})
	if rows != 6048 {
		panic("row count")
	}
}
