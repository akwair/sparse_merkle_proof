package main

import (
	"bytes"
	"crypto/sha256"
	"fmt"
	"math"
	"math/rand"
	"reflect"
	"testing"

	smt "github.com/celestiaorg/smt"
)

type applicationIntegrityStore struct {
	smt.MapStore
	name  string
	trace *[]string
}

func (s *applicationIntegrityStore) Get(key []byte) ([]byte, error) {
	*s.trace = append(*s.trace, fmt.Sprintf("%s:%x", s.name, key))
	return s.MapStore.Get(key)
}

func applicationIntegritySnapshot(t *testing.T, valueDomain string) (*ApplicationSnapshot, *[]string) {
	t.Helper()
	trace := new([]string)
	nodes := &applicationIntegrityStore{MapStore: smt.NewSimpleMap(), name: "node", trace: trace}
	values := &applicationIntegrityStore{MapStore: smt.NewSimpleMap(), name: "value", trace: trace}
	snapshot := &ApplicationSnapshot{tree: smt.NewSparseMerkleTree(nodes, values, sha256.New())}
	for i := 0; i < 3; i++ {
		key := sha256.Sum256([]byte(fmt.Sprintf("integrity/key/%d", i)))
		value := sha256.Sum256([]byte(fmt.Sprintf("integrity/%s/value/%d", valueDomain, i)))
		snapshot.keys = append(snapshot.keys, append([]byte(nil), key[:]...))
		if _, err := snapshot.tree.Update(key[:], value[:]); err != nil {
			t.Fatal(err)
		}
	}
	copy(snapshot.trustedRoot[:], snapshot.tree.Root())
	*trace = nil
	return snapshot, trace
}

func TestApplicationIntegrityDuplicateNativeReads(t *testing.T) {
	snapshot, trace := applicationIntegritySnapshot(t, "original")
	singleTraces := make([][]string, len(snapshot.keys))
	for rank := range snapshot.keys {
		*trace = nil
		if _, err := snapshot.Observe([]int{rank}); err != nil {
			t.Fatal(err)
		}
		path := sha256.Sum256(snapshot.keys[rank])
		if len(*trace) < 2 || (*trace)[0] != fmt.Sprintf("value:%x", path) {
			t.Fatalf("rank %d did not begin with one native value read: %v", rank, *trace)
		}
		for _, event := range (*trace)[1:] {
			if len(event) < 5 || event[:5] != "node:" {
				t.Fatalf("rank %d proof did not exclusively read nodes: %v", rank, *trace)
			}
		}
		singleTraces[rank] = append([]string(nil), (*trace)...)
	}
	indexes := []int{2, 0, 2, 1, 0, 0, 2, 1}
	var want []string
	for _, rank := range indexes {
		want = append(want, singleTraces[rank]...)
	}
	for observation := 0; observation < 2; observation++ {
		*trace = nil
		bundle, err := snapshot.Observe(indexes)
		if err != nil {
			t.Fatal(err)
		}
		if !reflect.DeepEqual(*trace, want) {
			t.Fatalf("observation %d changed ordered native Get+Prove reads: got %v want %v", observation, *trace, want)
		}
		if !snapshot.Accept(bundle, indexes) {
			t.Fatalf("observation %d returned invalid data", observation)
		}
	}
}

func TestApplicationIntegrityForeignValidRootRejected(t *testing.T) {
	trusted, _ := applicationIntegritySnapshot(t, "original")
	foreign, _ := applicationIntegritySnapshot(t, "foreign")
	indexes := []int{2, 0, 2, 1, 0, 0, 2, 1}
	bundle, err := foreign.Observe(indexes)
	if err != nil {
		t.Fatal(err)
	}
	if bytes.Equal(bundle.Root, trusted.trustedRoot[:]) || !verify(bundle) || !foreign.Accept(bundle, indexes) {
		t.Fatal("foreign fixture must be independently valid under a different root")
	}
	for i, rank := range indexes {
		if !bytes.Equal(bundle.Items[i].Key, trusted.keys[rank]) {
			t.Fatal("foreign fixture must retain the exact trusted request keys")
		}
	}
	if trusted.Accept(bundle, indexes) {
		t.Fatal("accepted a valid response authenticated by an untrusted root")
	}
}

func TestApplicationIntegrityReturnedBytesDetached(t *testing.T) {
	snapshot, _ := applicationIntegritySnapshot(t, "original")
	indexes := []int{2, 0, 2, 1, 0, 0, 2, 1}
	reference, err := snapshot.Observe(indexes)
	if err != nil {
		t.Fatal(err)
	}
	returned, err := snapshot.Observe(indexes)
	if err != nil {
		t.Fatal(err)
	}
	root := append([]byte(nil), snapshot.tree.Root()...)
	key := append([]byte(nil), snapshot.keys[2]...)
	returned.Root[0] ^= 1
	returned.Items[0].Key[0] ^= 1
	returned.Items[0].Value[0] ^= 1
	if !bytes.Equal(snapshot.trustedRoot[:], root) || !bytes.Equal(snapshot.tree.Root(), root) || !bytes.Equal(snapshot.keys[2], key) {
		t.Fatal("returned root/key mutation reached the trusted snapshot")
	}
	if !bytes.Equal(returned.Items[2].Key, reference.Items[2].Key) || !bytes.Equal(returned.Items[2].Value, reference.Items[2].Value) {
		t.Fatal("one returned item aliases a duplicate request item")
	}
	if snapshot.Accept(returned, indexes) || !snapshot.Accept(reference, indexes) {
		t.Fatal("returned mutation was accepted or corrupted an earlier response")
	}
	again, err := snapshot.Observe(indexes)
	if err != nil {
		t.Fatal(err)
	}
	if !equalBundle(reference, again) || !snapshot.Accept(again, indexes) {
		t.Fatal("returned key/value/root mutation changed a later observation")
	}
}

func TestApplicationIntegrityFullValueBlocks(t *testing.T) {
	for _, domain := range []string{"dev", "confirm"} {
		for _, index := range []int{0, 17, 4095} {
			var blocks [1024]byte
			for block := 0; block < 32; block++ {
				digest := sha256.Sum256([]byte(fmt.Sprintf("r7/%s/3407/value/%d/block/%d", domain, index, block)))
				copy(blocks[block*32:(block+1)*32], digest[:])
			}
			large, err := applicationValue(domain, index, 1000)
			if err != nil {
				t.Fatal(err)
			}
			small, err := applicationValue(domain, index, 32)
			if err != nil {
				t.Fatal(err)
			}
			if !bytes.Equal(large, blocks[:1000]) || !bytes.Equal(small, blocks[:32]) {
				t.Fatalf("value %s/%d differs from all 31 full blocks and the 8-byte final block", domain, index)
			}
		}
	}
}

func TestApplicationIntegrityContinuedSamplingOracle(t *testing.T) {
	// The oracle scans unnormalized masses instead of invoking the production
	// CDF or binary search. One PRNG continues through the registered loop order.
	rng := rand.New(rand.NewSource(3407))
	var wantSets []ApplicationRequestSet
	for _, domain := range []string{"dev", "confirm"} {
		for _, n := range []int{4096, 16384} {
			weights := make([]float64, n)
			total := 0.0
			for rank := range weights {
				weights[rank] = math.Pow(float64(rank+1), -0.99)
				total += weights[rank]
			}
			for _, distribution := range []string{"uniform", "zipf"} {
				for batch := 0; batch < 3; batch++ {
					indexes := make([]int, 128)
					for i := range indexes {
						if distribution == "uniform" {
							indexes[i] = rng.Intn(n)
							continue
						}
						target, cumulative := rng.Float64()*total, 0.0
						indexes[i] = n - 1
						for rank, weight := range weights {
							cumulative += weight
							if cumulative > target {
								indexes[i] = rank
								break
							}
						}
					}
					wantSets = append(wantSets, ApplicationRequestSet{Domain: domain, N: n, Distribution: distribution, Batch: batch, RequestSetID: fmt.Sprintf("%s_n%d_%s_b%d", domain, n, distribution, batch), RequestIndexes: indexes})
				}
			}
		}
	}
	gotSets, err := applicationRequestSets()
	if err != nil {
		t.Fatal(err)
	}
	if len(gotSets) != 24 {
		t.Fatalf("request sets=%d want 24", len(gotSets))
	}
	for i, want := range wantSets {
		if !reflect.DeepEqual(gotSets[i], want) {
			t.Fatalf("request set %d (%s) differs from independent continued-PRNG oracle", i, want.RequestSetID)
		}
	}
	plans, err := applicationPlans()
	if err != nil {
		t.Fatal(err)
	}
	if len(plans) != 192 {
		t.Fatalf("plans=%d want 192", len(plans))
	}
	i := 0
	for _, want := range wantSets {
		for _, size := range []int{32, 1000} {
			for _, q := range []int{1, 8, 32, 128} {
				plan := plans[i]
				config := ApplicationConfig{Domain: want.Domain, N: want.N, Q: q, ValueBytes: size, Distribution: want.Distribution, Batch: want.Batch}
				if plan.Config != config || plan.RequestSetID != want.RequestSetID || !reflect.DeepEqual(plan.RequestIndexes, want.RequestIndexes[:q]) {
					t.Fatalf("plan %d fails q/value pairing with the independent oracle", i)
				}
				i++
			}
		}
	}
}
