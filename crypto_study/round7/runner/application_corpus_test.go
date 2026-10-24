package main

import (
	"bytes"
	"crypto/sha256"
	"fmt"
	"reflect"
	"strings"
	"testing"

	smt "github.com/celestiaorg/smt"
)

// Reconstruct the new application matrix without calling the formal entry
// point or taking timestamps. Every tree is independently rebuilt from its
// checkpoint; every native bundle is encoded/decoded under all nine modes.
func TestApplicationCorpus(t *testing.T) {
	plans, err := applicationPlans()
	if err != nil {
		t.Fatal(err)
	}
	runner := NewEncoder()
	treeCount, bundleCount, modeCount, frameCount := 0, 0, 0, 0
	pairKeys := map[string][][]byte{}
	for _, domain := range []string{"dev", "confirm"} {
		for _, n := range []int{4096, 16384} {
			for _, valueBytes := range []int{32, 1000} {
				snapshot, cp, err := newApplicationSnapshot(domain, n, valueBytes)
				if err != nil {
					t.Fatal(err)
				}
				treeCount++
				if cp.Domain != domain || cp.N != n || cp.ValueBytes != valueBytes || len(cp.Root) != 32 || len(cp.Keys) != n || len(cp.Values) != n {
					t.Fatal("checkpoint shape")
				}
				rebuild := smt.NewSparseMerkleTree(smt.NewSimpleMap(), smt.NewSimpleMap(), sha256.New())
				var prefixes [16]int
				for i, key := range cp.Keys {
					if !bytes.Equal(key, hash(fmt.Sprintf("r7/%s/3407/key/%d", domain, i))) || len(cp.Values[i]) != valueBytes {
						t.Fatal("checkpoint key/value derivation")
					}
					prefixes[workloadPathPrefix(key)]++
					if _, err := rebuild.Update(key, cp.Values[i]); err != nil {
						t.Fatal(err)
					}
				}
				if !bytes.Equal(rebuild.Root(), cp.Root) || prefixes != cp.MemberPrefixCounts {
					t.Fatal("checkpoint independent reconstruction")
				}
				pair := fmt.Sprintf("%s_%d", domain, n)
				if prior, ok := pairKeys[pair]; ok {
					if !reflect.DeepEqual(prior, cp.Keys) {
						t.Fatal("keys changed with value size")
					}
				} else {
					pairKeys[pair] = make([][]byte, len(cp.Keys))
					for i, key := range cp.Keys {
						pairKeys[pair][i] = append([]byte(nil), key...)
					}
				}
				for _, p := range plans {
					c := p.Config
					if c.Domain != domain || c.N != n || c.ValueBytes != valueBytes {
						continue
					}
					reference, err := snapshot.Observe(p.RequestIndexes)
					if err != nil {
						t.Fatal(err)
					}
					if !snapshot.Accept(reference, p.RequestIndexes) {
						t.Fatal("native reference rejected")
					}
					bundleCount++
					wires := map[string][]byte{}
					sizes := map[string]int{}
					for _, mode := range studyModes {
						raw, err := runner.Encode(reference, mode)
						if err != nil {
							t.Fatal(err)
						}
						out, err := decodeStudy(raw, mode)
						if err != nil {
							t.Fatal(err)
						}
						if !equalBundle(reference, out) || !snapshot.Accept(out, p.RequestIndexes) {
							t.Fatalf("%s mode %s restoration", p.ID, mode)
						}
						wires[mode], sizes[mode] = raw, len(raw)
						modeCount++
						if strings.HasPrefix(mode, "reset-") {
							if !bytes.Equal(raw, wires[strings.TrimPrefix(mode, "reset-")]) {
								t.Fatal("fresh/reset corpus mismatch")
							}
						} else {
							frameCount++
						}
					}
					diag := applicationStructure(p, reference, sizes)
					if diag["domain"] != domain || diag["value_bytes"] != valueBytes || diag["distribution"] != c.Distribution || diag["q"] != c.Q {
						t.Fatal("diagnostic metadata")
					}
					occurrences := diag["request_prefix_counts"].([16]int)
					uniquePrefixes := diag["unique_request_prefix_counts"].([16]int)
					count, unique := 0, 0
					for i := range occurrences {
						count += occurrences[i]
						unique += uniquePrefixes[i]
					}
					if count != c.Q || unique != diag["unique_query_count"].(int) || unique > c.Q || unique < 1 {
						t.Fatal("query diagnostic accounting")
					}
				}
				// Checkpoint mutation must not mutate snapshot keys, root or values.
				cp.Root[0] ^= 1
				cp.Keys[0][0] ^= 1
				cp.Values[0][0] ^= 1
				out, err := snapshot.Observe([]int{0})
				if err != nil {
					t.Fatal(err)
				}
				if !snapshot.Accept(out, []int{0}) {
					t.Fatal("checkpoint aliases trusted snapshot")
				}
				t.Logf("reconstructed %s N=%d value_bytes=%d: 24 bundles", domain, n, valueBytes)
			}
		}
	}
	if treeCount != 8 || bundleCount != 192 || modeCount != 1728 || frameCount != 1152 || bundleCount*21*len(studyModes) != 36288 {
		t.Fatalf("counts trees=%d bundles=%d modes=%d frames=%d", treeCount, bundleCount, modeCount, frameCount)
	}
}

func TestApplicationInvalidSnapshotsAndRequestSets(t *testing.T) {
	for _, args := range []struct {
		domain string
		n, v   int
	}{{"bad", 4096, 32}, {"dev", 0, 32}, {"dev", 4096, 31}} {
		if _, _, err := newApplicationSnapshot(args.domain, args.n, args.v); err == nil {
			t.Fatal("invalid snapshot accepted")
		}
	}
	if _, err := applicationPlansFromSets([]ApplicationRequestSet{{Domain: "dev", N: 4096, Distribution: "uniform", RequestIndexes: []int{0}}}); err == nil {
		t.Fatal("short request set accepted")
	}
}
