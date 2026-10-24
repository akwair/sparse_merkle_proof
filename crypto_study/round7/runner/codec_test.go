package main

import (
	"bytes"
	"compress/zlib"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	smt "github.com/celestiaorg/smt"
)

func studyFixture(t *testing.T, domain string) Bundle {
	t.Helper()
	tree := smt.NewSparseMerkleTree(smt.NewSimpleMap(), smt.NewSimpleMap(), sha256.New())
	for i := 0; i < 64; i++ {
		_, err := tree.Update(hash(fmt.Sprintf("codec/%s/key/%d", domain, i)), hash(fmt.Sprintf("codec/%s/value/%d", domain, i)))
		if err != nil {
			t.Fatal(err)
		}
	}
	b := Bundle{Root: tree.Root()}
	for i := 0; i < 10; i++ {
		key := hash(fmt.Sprintf("codec/%s/key/%d", domain, i))
		value := hash(fmt.Sprintf("codec/%s/value/%d", domain, i))
		if i >= 8 {
			key = hash(fmt.Sprintf("codec/%s/absent/%d", domain, i))
			value = nil
		}
		p, err := tree.Prove(key)
		if err != nil {
			t.Fatal(err)
		}
		b.Items = append(b.Items, Item{Key: key, Value: value, Proof: p})
	}
	if !verify(b) {
		t.Fatal("invalid fixture")
	}
	return b
}

func TestStudyDefaultAndModeList(t *testing.T) {
	want := []string{"ordinary", "compact", "dictionary", "zlib-ordinary", "zlib-compact", "zlib-dictionary", "reset-zlib-ordinary", "reset-zlib-compact", "reset-zlib-dictionary"}
	if fmt.Sprint(studyModes) != fmt.Sprint(want) {
		t.Fatalf("mode list: %v", studyModes)
	}
	b := studyFixture(t, "default")
	a, err := NewEncoder().Encode(b, "")
	if err != nil {
		t.Fatal(err)
	}
	c, err := encode(b, "ordinary")
	if err != nil || !bytes.Equal(a, c) {
		t.Fatal("default changed")
	}
	out, err := decodeStudy(a, "")
	if err != nil || !equalBundle(out, b) || !verify(out) {
		t.Fatal("default decode")
	}
	if _, err = NewEncoder().Encode(b, "unknown"); err == nil {
		t.Fatal("unknown encode mode")
	}
	if _, err = decodeStudy(a, "unknown"); err == nil {
		t.Fatal("unknown decode mode")
	}
}

func TestStudyRoundTripsAllModes(t *testing.T) {
	b := studyFixture(t, "roundtrip")
	enc := NewEncoder()
	for _, mode := range studyModes {
		t.Run(mode, func(t *testing.T) {
			w, err := enc.Encode(b, mode)
			if err != nil {
				t.Fatal(err)
			}
			got, err := decodeStudy(w, mode)
			if err != nil || !equalBundle(b, got) || !verify(got) {
				t.Fatalf("roundtrip: %v", err)
			}
			for _, wrongMode := range studyModes {
				if strings.TrimPrefix(wrongMode, "reset-") == strings.TrimPrefix(mode, "reset-") {
					continue
				}
				if _, err = decodeStudy(w, wrongMode); err == nil {
					t.Fatalf("accepted wrong mode %s", wrongMode)
				}
			}
			got.Items[0].Value = []byte("tampered")
			if verify(got) {
				t.Fatal("tampered value accepted")
			}
			got, _ = decodeStudy(w, mode)
			got.Items[0].Key = hash("tampered key")
			if verify(got) {
				t.Fatal("tampered key accepted")
			}
			got, _ = decodeStudy(w, mode)
			got.Root = append([]byte{}, got.Root...)
			got.Root[0] ^= 1
			if verify(got) {
				t.Fatal("tampered root accepted")
			}
		})
	}
}

func TestStudyDictionaryIdentity(t *testing.T) {
	for _, domain := range []string{"identity-a", "identity-b"} {
		b := studyFixture(t, domain)
		for _, q := range []int{1, len(b.Items)} {
			x := Bundle{Root: b.Root, Items: b.Items[:q]}
			s, unique := 0, map[string]bool{}
			for _, it := range x.Items {
				for _, node := range it.Proof.SideNodes {
					s++
					unique[string(node)] = true
				}
			}
			a, err := encode(x, "ordinary")
			if err != nil {
				t.Fatal(err)
			}
			d, err := NewEncoder().Encode(x, "dictionary")
			if err != nil {
				t.Fatal(err)
			}
			if len(a)-len(d) != 30*s-32*len(unique)-2 {
				t.Fatalf("identity S=%d U=%d: %d", s, len(unique), len(a)-len(d))
			}
		}
	}
}

func TestStudyResetHistoryAndDetachedOutputs(t *testing.T) {
	enc := NewEncoder()
	a, b := studyFixture(t, "reset-a"), studyFixture(t, "reset-b")
	for _, base := range []string{"ordinary", "compact", "dictionary"} {
		var old, saved []byte
		for _, x := range []Bundle{a, b, a} {
			fresh, err := enc.Encode(x, "zlib-"+base)
			if err != nil {
				t.Fatal(err)
			}
			reset, err := enc.Encode(x, "reset-zlib-"+base)
			if err != nil {
				t.Fatal(err)
			}
			if !bytes.Equal(fresh, reset) {
				t.Fatalf("retained history or changed stream: %s", base)
			}
			if old != nil && !bytes.Equal(old, saved) {
				t.Fatalf("output aliased reusable buffer: %s", base)
			}
			out, err := decodeStudy(reset, "reset-zlib-"+base)
			if err != nil || !verify(out) || !equalBundle(out, x) {
				t.Fatalf("reset frame: %v", err)
			}
			old = reset
			saved = append([]byte{}, reset...)
		}
	}
}

func TestStudyFramesRejectTruncationTrailingAndOversize(t *testing.T) {
	b := studyFixture(t, "bounds")
	enc := NewEncoder()
	for _, mode := range studyModes {
		t.Run(mode, func(t *testing.T) {
			w, err := enc.Encode(b, mode)
			if err != nil {
				t.Fatal(err)
			}
			for _, bad := range [][]byte{nil, w[:3], w[:4], w[:len(w)-1], append(append([]byte{}, w...), 0), make([]byte, maxWire+1)} {
				if _, err := decodeStudy(bad, mode); err == nil {
					t.Fatal("malformed frame accepted")
				}
			}
		})
	}
}

// Parser-only fixtures below deliberately have no valid root; they never enter
// workload generation or a performance run.
func parserOnlyBundle(nodes [][]byte) Bundle {
	return Bundle{Root: make([]byte, 32), Items: []Item{{Key: []byte{1}, Value: []byte{2}, Proof: smt.SparseMerkleProof{SideNodes: nodes}}}}
}

func TestStudyDictionaryStrictFieldsAndIndices(t *testing.T) {
	b := parserOnlyBundle([][]byte{make([]byte, 32)})
	w, err := NewEncoder().Encode(b, "dictionary")
	if err != nil {
		t.Fatal(err)
	}
	// Dictionary body: U16, U*32-byte hashes, root32, count16, then items.
	const countPos = 4 + 2 + 32 + 32
	const indexPos = countPos + 2 + 3 + 3 + 2
	for _, tc := range []struct {
		name string
		pos  int
		val  uint16
	}{
		{"empty count", countPos, 0}, {"count overflow", countPos, 257},
		{"key length", countPos + 2, 4097}, {"depth overflow", indexPos - 2, 257},
		{"index overflow", indexPos, 1},
	} {
		t.Run(tc.name, func(t *testing.T) {
			bad := append([]byte{}, w...)
			binary.BigEndian.PutUint16(bad[tc.pos:], tc.val)
			if _, err := decodeStudy(bad, "dictionary"); err == nil {
				t.Fatal("invalid dictionary accepted")
			}
		})
	}
	for _, mutate := range []func(*Bundle){
		func(x *Bundle) { x.Root = nil },
		func(x *Bundle) { x.Items = nil },
		func(x *Bundle) { x.Items = make([]Item, 257) },
		func(x *Bundle) { x.Items[0].Key = make([]byte, 4097) },
		func(x *Bundle) { x.Items[0].Value = make([]byte, 4097) },
		func(x *Bundle) { x.Items[0].Proof.SideNodes = [][]byte{{1}} },
		func(x *Bundle) { x.Items[0].Proof.SideNodes = make([][]byte, 257) },
		func(x *Bundle) { x.Items[0].Proof.NonMembershipLeafData = make([]byte, 66) },
		func(x *Bundle) { x.Items[0].Proof.SiblingData = make([]byte, 66) },
	} {
		x := parserOnlyBundle([][]byte{make([]byte, 32)})
		mutate(&x)
		if _, err := NewEncoder().Encode(x, "dictionary"); err == nil {
			t.Fatal("invalid input accepted")
		}
	}
	// Exactly 65536 distinct hashes cannot be numbered using a uint16 count.
	x := Bundle{Root: make([]byte, 32)}
	for i := 0; i < 256; i++ {
		it := Item{Key: []byte{byte(i)}, Value: []byte{1}}
		for j := 0; j < 256; j++ {
			node := make([]byte, 32)
			binary.BigEndian.PutUint32(node, uint32(i*256+j))
			it.Proof.SideNodes = append(it.Proof.SideNodes, node)
		}
		x.Items = append(x.Items, it)
	}
	if _, err := NewEncoder().Encode(x, "dictionary"); err == nil {
		t.Fatal("dictionary uint16 overflow accepted")
	}
}

func TestStudyDictionaryZeroDepthAndBoundaries(t *testing.T) {
	// A one-leaf native tree produces a legitimate zero-depth member proof.
	tree := smt.NewSparseMerkleTree(smt.NewSimpleMap(), smt.NewSimpleMap(), sha256.New())
	_, err := tree.Update([]byte("only"), []byte("value"))
	if err != nil {
		t.Fatal(err)
	}
	p, err := tree.Prove([]byte("only"))
	if err != nil {
		t.Fatal(err)
	}
	b := Bundle{Root: tree.Root(), Items: []Item{{Key: []byte("only"), Value: []byte("value"), Proof: p}}}
	for _, m := range studyModes {
		w, err := NewEncoder().Encode(b, m)
		if err != nil {
			t.Fatal(err)
		}
		out, err := decodeStudy(w, m)
		if err != nil || !verify(out) || !equalBundle(b, out) {
			t.Fatalf("empty dictionary %s: %v", m, err)
		}
	}
	// Maximum item/node counts and field lengths remain parseable.
	x := parserOnlyBundle(make([][]byte, 256))
	x.Items[0].Key = make([]byte, 4096)
	x.Items[0].Value = make([]byte, 4096)
	for i := range x.Items[0].Proof.SideNodes {
		x.Items[0].Proof.SideNodes[i] = make([]byte, 32)
	}
	one := x.Items[0]
	x.Items = make([]Item, 256)
	for i := range x.Items {
		x.Items[i] = one
	}
	w, err := NewEncoder().Encode(x, "dictionary")
	if err != nil {
		t.Fatal(err)
	}
	out, err := decodeStudy(w, "dictionary")
	if err != nil || !equalBundle(x, out) {
		t.Fatalf("boundary: %v", err)
	}
}

func TestStudyCompressedPayloadLimitAndTrailing(t *testing.T) {
	b := studyFixture(t, "compressed-limit")
	for _, base := range []string{"ordinary", "compact", "dictionary"} {
		mode := "zlib-" + base
		good, err := NewEncoder().Encode(b, mode)
		if err != nil {
			t.Fatal(err)
		}
		var out bytes.Buffer
		writer, err := zlib.NewWriterLevel(&out, 6)
		if err != nil {
			t.Fatal(err)
		}
		if _, err = writer.Write(make([]byte, maxWire+1)); err != nil {
			t.Fatal(err)
		}
		if err = writer.Close(); err != nil {
			t.Fatal(err)
		}
		bad := append(append([]byte{}, good[:4]...), out.Bytes()...)
		if _, err = decodeStudy(bad, mode); err == nil {
			t.Fatal("inflate limit accepted")
		}
		joined := append(append([]byte{}, good...), good[4:]...)
		if _, err = decodeStudy(joined, mode); err == nil {
			t.Fatal("concatenated zlib accepted")
		}
	}
}

func TestStudyLegacy288ArchivedFrames(t *testing.T) {
	paths, err := filepath.Glob(filepath.FromSlash("../../round3_qpc/runs/screening_001/external/*/bundle.json"))
	if err != nil || len(paths) != 72 {
		t.Fatalf("expected 72 archived bundles, got %d: %v", len(paths), err)
	}
	count := 0
	for _, p := range paths {
		raw, err := os.ReadFile(p)
		if err != nil {
			t.Fatal(err)
		}
		var b Bundle
		if err = json.Unmarshal(raw, &b); err != nil {
			t.Fatal(err)
		}
		if !verify(b) {
			t.Fatalf("source proof invalid: %s", p)
		}
		for _, m := range modes {
			want, err := os.ReadFile(filepath.Join(filepath.Dir(p), m+".wire"))
			if err != nil {
				t.Fatal(err)
			}
			got, err := NewEncoder().Encode(b, m)
			if err != nil || !bytes.Equal(want, got) {
				t.Fatalf("baseline changed %s/%s: %v", p, m, err)
			}
			out, err := decodeStudy(want, m)
			if err != nil || !equalBundle(b, out) || !verify(out) {
				t.Fatalf("baseline restore %s: %v", p, err)
			}
			count++
		}
	}
	if count != 288 {
		t.Fatalf("replayed %d", count)
	}
	t.Logf("exactly replayed %d archived frames from %d bundles", count, len(paths))
}
