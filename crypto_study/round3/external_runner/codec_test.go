package main

import (
	"bytes"
	"crypto/sha256"
	smt "github.com/celestiaorg/smt"
	"testing"
)

func TestRoundTripModes(t *testing.T) {
	tree := smt.NewSparseMerkleTree(smt.NewSimpleMap(), smt.NewSimpleMap(), sha256.New())
	key := []byte("present")
	value := []byte("value")
	if _, e := tree.Update(key, value); e != nil {
		t.Fatal(e)
	}
	for _, k := range [][]byte{key, []byte("absent")} {
		v := value
		if !bytes.Equal(k, key) {
			v = nil
		}
		p, e := tree.Prove(k)
		if e != nil {
			t.Fatal(e)
		}
		b := Bundle{Root: tree.Root(), Items: []Item{{Key: k, Value: v, Proof: p}}}
		for _, mode := range modes {
			w, e := encode(b, mode)
			if e != nil {
				t.Fatal(e)
			}
			got, e := decode(w, mode)
			if e != nil {
				t.Fatal(e)
			}
			if !equalBundle(b, got) || !verify(got) {
				t.Fatalf("roundtrip %s", mode)
			}
			got.Items[0].Value = []byte("tampered")
			if verify(got) {
				t.Fatal("tamper accepted")
			}
			for _, bad := range [][]byte{nil, w[:4], w[:len(w)-1], append(append([]byte{}, w...), 0)} {
				if _, e = decode(bad, mode); e == nil {
					t.Fatalf("bad frame accepted %s", mode)
				}
			}
		}
	}
}

func TestSizeIdentity(t *testing.T) {
	tree := smt.NewSparseMerkleTree(smt.NewSimpleMap(), smt.NewSimpleMap(), sha256.New())
	for i := 0; i < 40; i++ {
		k := []byte{byte(i)}
		if _, e := tree.Update(k, []byte{1}); e != nil {
			t.Fatal(e)
		}
	}
	for i := 0; i < 42; i++ {
		k := []byte{byte(i)}
		p, e := tree.Prove(k)
		if e != nil {
			t.Fatal(e)
		}
		c, e := smt.CompactProof(p, sha256.New())
		if e != nil {
			t.Fatal(e)
		}
		b := Bundle{Root: tree.Root(), Items: []Item{{Key: k, Value: []byte{1}, Proof: p}}}
		a, _ := encode(b, "ordinary")
		z, _ := encode(b, "compact")
		if len(a)-len(z) != 32*(len(p.SideNodes)-len(c.SideNodes))-2-len(c.BitMask) {
			t.Fatal("byte identity")
		}
	}
}
