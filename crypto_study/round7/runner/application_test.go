package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"math"
	"math/rand"
	"os"
	"reflect"
	"strings"
	"testing"

	smt "github.com/celestiaorg/smt"
)

func TestApplicationFiniteZipfCDF(t *testing.T) {
	cdf, err := applicationZipfCDF(3, 0.99)
	if err != nil {
		t.Fatal(err)
	}
	sum := 1 + math.Pow(2, -0.99) + math.Pow(3, -0.99)
	want := []float64{1 / sum, (1 + math.Pow(2, -0.99)) / sum, 1}
	for i := range want {
		if math.Abs(cdf[i]-want[i]) > 1e-15 {
			t.Fatalf("cdf[%d]=%.17g want %.17g", i, cdf[i], want[i])
		}
	}
	for _, tc := range []struct {
		u    float64
		want int
	}{{0, 0}, {math.Nextafter(cdf[0], 0), 0}, {cdf[0], 1}, {cdf[1], 2}, {math.Nextafter(1, 0), 2}} {
		if got := applicationZipfRank(cdf, tc.u); got != tc.want {
			t.Fatalf("rank(%g)=%d want %d", tc.u, got, tc.want)
		}
	}
	for _, n := range []int{-1, 0} {
		if _, err := applicationZipfCDF(n, 0.99); err == nil {
			t.Fatalf("accepted n=%d", n)
		}
	}
	for _, theta := range []float64{0, -1, math.NaN(), math.Inf(1)} {
		if _, err := applicationZipfCDF(4, theta); err == nil {
			t.Fatalf("accepted theta=%g", theta)
		}
	}
}

func TestApplicationRanksDeterministicAndWithReplacement(t *testing.T) {
	for _, distribution := range []string{"uniform", "zipf"} {
		a, err := applicationSampleRanks(rand.New(rand.NewSource(3407)), 2, distribution, 128)
		if err != nil {
			t.Fatal(err)
		}
		b, err := applicationSampleRanks(rand.New(rand.NewSource(3407)), 2, distribution, 128)
		if err != nil {
			t.Fatal(err)
		}
		if !reflect.DeepEqual(a, b) || len(a) != 128 {
			t.Fatal("request sequence is not deterministic or has wrong count")
		}
		seen := map[int]bool{}
		for _, i := range a {
			if i < 0 || i >= 2 {
				t.Fatal("out-of-range rank")
			}
			seen[i] = true
		}
		if len(seen) != 2 {
			t.Fatal("expected both ranks with repeated queries")
		}
	}
	if _, err := applicationSampleRanks(rand.New(rand.NewSource(3407)), 10, "other", 128); err == nil {
		t.Fatal("accepted unknown distribution")
	}
}

func TestApplicationConfigurationBoundaries(t *testing.T) {
	good := ApplicationConfig{Domain: "dev", N: 4096, Q: 8, ValueBytes: 32, Distribution: "uniform", Batch: 0}
	if err := good.Validate(); err != nil {
		t.Fatal(err)
	}
	for _, mutate := range []func(*ApplicationConfig){func(c *ApplicationConfig) { c.Domain = "" }, func(c *ApplicationConfig) { c.Domain = "other" }, func(c *ApplicationConfig) { c.N = 0 }, func(c *ApplicationConfig) { c.N = 4095 }, func(c *ApplicationConfig) { c.Q = 0 }, func(c *ApplicationConfig) { c.Q = 2 }, func(c *ApplicationConfig) { c.Q = 129 }, func(c *ApplicationConfig) { c.ValueBytes = 0 }, func(c *ApplicationConfig) { c.ValueBytes = 33 }, func(c *ApplicationConfig) { c.Distribution = "" }, func(c *ApplicationConfig) { c.Batch = -1 }, func(c *ApplicationConfig) { c.Batch = 3 }} {
		c := good
		mutate(&c)
		if c.Validate() == nil {
			t.Fatalf("accepted invalid configuration: %+v", c)
		}
	}
}

func TestApplicationValuePrefixes(t *testing.T) {
	for _, domain := range []string{"dev", "confirm"} {
		small, err := applicationValue(domain, 17, 32)
		if err != nil {
			t.Fatal(err)
		}
		large, err := applicationValue(domain, 17, 1000)
		if err != nil {
			t.Fatal(err)
		}
		if len(small) != 32 || len(large) != 1000 || !bytes.Equal(small, large[:32]) {
			t.Fatal("value size or prefix pairing changed")
		}
		if !bytes.Equal(small, hash("r7/"+domain+"/3407/value/17/block/0")) {
			t.Fatal("value derivation changed")
		}
	}
	for _, n := range []int{0, 31, 33, 999, 1001} {
		if _, err := applicationValue("dev", 0, n); err == nil {
			t.Fatalf("accepted value size %d", n)
		}
	}
	if _, err := applicationValue("other", 0, 32); err == nil {
		t.Fatal("accepted domain")
	}
	if _, err := applicationValue("dev", -1, 32); err == nil {
		t.Fatal("accepted negative index")
	}
}

func TestApplicationMatrixPairing(t *testing.T) {
	plans, err := applicationPlans()
	if err != nil {
		t.Fatal(err)
	}
	again, err := applicationPlans()
	if err != nil {
		t.Fatal(err)
	}
	if len(plans) != 192 || !reflect.DeepEqual(plans, again) {
		t.Fatal("matrix size or determinism")
	}
	ids := map[string]bool{}
	prefixes := map[string][]int{}
	cells := map[string]int{}
	for _, p := range plans {
		if err := p.Config.Validate(); err != nil {
			t.Fatal(err)
		}
		if len(p.RequestIndexes) != p.Config.Q || ids[p.ID] {
			t.Fatal("request size or duplicate id")
		}
		ids[p.ID] = true
		cells[p.Cell]++
		key := p.RequestSetID
		prior := prefixes[key]
		if len(prior) > len(p.RequestIndexes) {
			if !reflect.DeepEqual(prior[:len(p.RequestIndexes)], p.RequestIndexes) {
				t.Fatal("q/value prefix differs")
			}
		} else {
			if prior != nil && !reflect.DeepEqual(prior, p.RequestIndexes[:len(prior)]) {
				t.Fatal("q/value prefix differs")
			}
			prefixes[key] = p.RequestIndexes
		}
	}
	if len(prefixes) != 24 || len(cells) != 32 {
		t.Fatalf("sets=%d cells=%d", len(prefixes), len(cells))
	}
	for _, count := range cells {
		if count != 6 {
			t.Fatalf("cell has %d domain/batch entries", count)
		}
	}
}

func tinyApplicationSnapshot(t *testing.T) *ApplicationSnapshot {
	t.Helper()
	tree := smt.NewSparseMerkleTree(smt.NewSimpleMap(), smt.NewSimpleMap(), sha256.New())
	keys := [][]byte{hash("test-key-a"), hash("test-key-b"), hash("test-key-c")}
	for i, k := range keys {
		if _, err := tree.Update(k, hash(string(rune('a'+i)))); err != nil {
			t.Fatal(err)
		}
	}
	var root [32]byte
	copy(root[:], tree.Root())
	return &ApplicationSnapshot{tree: tree, keys: keys, trustedRoot: root}
}

func TestApplicationDuplicatesAndTrustedValidation(t *testing.T) {
	snapshot := tinyApplicationSnapshot(t)
	indexes := []int{2, 0, 2, 1, 0, 0, 2, 1}
	b, err := snapshot.Observe(indexes)
	if err != nil {
		t.Fatal(err)
	}
	if len(b.Items) != len(indexes) || !snapshot.Accept(b, indexes) {
		t.Fatal("did not accept exact ordered result")
	}
	for i, idx := range indexes {
		if !bytes.Equal(b.Items[i].Key, snapshot.keys[idx]) {
			t.Fatal("query order changed")
		}
	}
	b.Root[0] ^= 1
	if snapshot.Accept(b, indexes) {
		t.Fatal("accepted altered root")
	}
	b, err = snapshot.Observe(indexes)
	if err != nil {
		t.Fatal(err)
	}
	if !snapshot.Accept(b, indexes) {
		t.Fatal("returned root aliased immutable trusted root")
	}
	b.Items[0], b.Items[1] = b.Items[1], b.Items[0]
	if snapshot.Accept(b, indexes) {
		t.Fatal("accepted reordered keys")
	}
	if snapshot.Accept(Bundle{Root: snapshot.trustedRoot[:]}, nil) {
		t.Fatal("accepted empty response")
	}
	for _, bad := range [][]int{nil, {}, {-1}, {3}} {
		if _, err := snapshot.Observe(bad); err == nil {
			t.Fatalf("accepted invalid requests %v", bad)
		}
	}
	b, err = snapshot.Observe(indexes)
	if err != nil {
		t.Fatal(err)
	}
	if snapshot.Accept(b, indexes[:len(indexes)-1]) {
		t.Fatal("accepted wrong request count")
	}
	// Each repeated observation must perform new native Get/Prove calls, not
	// return a previously cached answer: a changed backing value changes output.
	if _, err := snapshot.tree.Update(snapshot.keys[0], hash("changed")); err != nil {
		t.Fatal(err)
	}
	changed, err := snapshot.Observe(indexes)
	if err != nil {
		t.Fatal(err)
	}
	if bytes.Equal(changed.Items[1].Value, b.Items[1].Value) {
		t.Fatal("observation reused cached values")
	}
	if snapshot.Accept(changed, indexes) {
		t.Fatal("accepted snapshot mutation under original trusted root")
	}
}

func TestApplicationAllModesRepeatedQueryEquality(t *testing.T) {
	snapshot := tinyApplicationSnapshot(t)
	indexes := []int{2, 0, 2, 1, 0, 0, 2, 1}
	b, err := snapshot.Observe(indexes)
	if err != nil {
		t.Fatal(err)
	}
	runner := NewEncoder()
	wires := map[string][]byte{}
	for _, mode := range studyModes {
		raw, err := runner.Encode(b, mode)
		if err != nil {
			t.Fatal(err)
		}
		out, err := decodeStudy(raw, mode)
		if err != nil {
			t.Fatal(err)
		}
		if !equalBundle(b, out) || !snapshot.Accept(out, indexes) {
			t.Fatalf("failed %s restoration", mode)
		}
		wires[mode] = raw
		fresh, err := NewEncoder().Encode(b, mode)
		if err != nil || !bytes.Equal(raw, fresh) {
			t.Fatalf("fresh encoder differs %s", mode)
		}
		again, err := runner.Encode(b, mode)
		if err != nil || !bytes.Equal(raw, again) {
			t.Fatalf("sequential encoder differs %s", mode)
		}
		if strings.HasPrefix(mode, "reset-") && !bytes.Equal(raw, wires[strings.TrimPrefix(mode, "reset-")]) {
			t.Fatalf("reset differs %s", mode)
		}
	}
}

func TestApplicationDefaultPathBytePreservation(t *testing.T) {
	source, err := os.ReadFile("main.go")
	if err != nil {
		t.Fatal(err)
	}
	insertion := "\tif len(os.Args) > 1 && os.Args[1] == \"--application\" {\n\t\trunApplication(os.Args[2:])\n\t\treturn\n\t}\n"
	normalized := strings.ReplaceAll(string(source), "\r\n", "\n")
	if strings.Count(normalized, insertion) != 1 {
		t.Fatal("missing minimal application dispatch")
	}
	restored := strings.Replace(normalized, insertion, "", 1)
	sum := sha256.Sum256([]byte(restored))
	if hex.EncodeToString(sum[:]) != "c7f4f36fdfad8f954344e039c095017bbdc84ca00fed1a89c8e8fe4166aaede9" {
		t.Fatal("original main body was changed")
	}
}

func TestApplicationInvalidCLIAndExclusiveDirectory(t *testing.T) {
	for _, args := range [][]string{nil, {""}, {"a", "b"}, {t.TempDir()}} {
		func() {
			defer func() {
				if recover() == nil {
					t.Fatalf("accepted invalid/existing workdir: %v", args)
				}
			}()
			runApplication(args)
		}()
	}
}
