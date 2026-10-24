package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"reflect"
	"strings"
	"sync"
	"testing"

	smt "github.com/celestiaorg/smt"
)

var workloadFixtureOnce sync.Once
var workloadFixture []Workload
var workloadCheckpoint TreeCheckpoint
var workloadFixtureError error

func loadWorkloadFixture(t *testing.T) ([]Workload, TreeCheckpoint) {
	t.Helper()
	workloadFixtureOnce.Do(func() {
		workloadFixture, workloadCheckpoint, workloadFixtureError = MakeWorkloads("dev", 4096)
	})
	if workloadFixtureError != nil {
		t.Fatalf("MakeWorkloads(dev,4096): %v", workloadFixtureError)
	}
	return workloadFixture, workloadCheckpoint
}

func TestMakeWorkloadsMatrix(t *testing.T) {
	ws, cp := loadWorkloadFixture(t)
	if len(ws) != 48 || cp.Domain != "dev" || cp.N != 4096 {
		t.Fatalf("wrong matrix/checkpoint: workloads=%d domain=%s N=%d", len(ws), cp.Domain, cp.N)
	}
	cells := map[string]int{}
	ids := map[string]bool{}
	for _, w := range ws {
		wantCell := fmt.Sprintf("n4096_q%d_%s_%s", w.Q, w.Kind, w.Pattern)
		wantID := fmt.Sprintf("dev_%s_b%d", wantCell, w.Batch)
		if w.Domain != "dev" || w.N != 4096 || w.Cell != wantCell || w.ID != wantID || ids[w.ID] {
			t.Fatalf("invalid or duplicate workload metadata: %+v", w)
		}
		ids[w.ID] = true
		if w.Q != 1 && w.Q != 8 && w.Q != 32 && w.Q != 128 {
			t.Fatalf("unexpected q: %d", w.Q)
		}
		if (w.Kind != "member" && w.Kind != "absent") || (w.Pattern != "dispersed" && w.Pattern != "clustered") || w.Batch < 0 || w.Batch > 2 {
			t.Fatalf("invalid matrix dimensions: %s", w.ID)
		}
		if len(w.Bundle.Items) != w.Q || !bytes.Equal(w.Bundle.Root, cp.Root) {
			t.Fatalf("wrong item count or root: %s", w.ID)
		}
		cells[w.Cell]++
	}
	if len(cells) != 16 {
		t.Fatalf("cells=%d want 16", len(cells))
	}
	for cell, count := range cells {
		if count != 3 {
			t.Fatalf("%s has %d batches, want 3", cell, count)
		}
	}
}

func TestWorkloadCheckpointRebuildAndMembership(t *testing.T) {
	ws, cp := loadWorkloadFixture(t)
	if len(cp.Keys) != cp.N || len(cp.Values) != cp.N || len(cp.Root) != 32 {
		t.Fatal("incomplete replay checkpoint")
	}
	tree := smt.NewSparseMerkleTree(smt.NewSimpleMap(), smt.NewSimpleMap(), sha256.New())
	members := map[string][]byte{}
	var counts [16]int
	for i, key := range cp.Keys {
		wantKey := sha256.Sum256([]byte(fmt.Sprintf("r4/dev/3407/key/%d", i)))
		wantValue := sha256.Sum256([]byte(fmt.Sprintf("r4/dev/3407/value/%d", i)))
		if !bytes.Equal(key, wantKey[:]) || !bytes.Equal(cp.Values[i], wantValue[:]) {
			t.Fatalf("checkpoint derivation mismatch at %d", i)
		}
		if _, exists := members[string(key)]; exists {
			t.Fatal("duplicate member key")
		}
		members[string(key)] = cp.Values[i]
		path := sha256.Sum256(key)
		counts[path[0]>>4]++
		if _, err := tree.Update(key, cp.Values[i]); err != nil {
			t.Fatal(err)
		}
	}
	if !bytes.Equal(tree.Root(), cp.Root) || counts != cp.MemberPrefixCounts {
		t.Fatal("checkpoint root or actual-path occupancy mismatch")
	}
	for _, w := range ws {
		for _, item := range w.Bundle.Items {
			value, exists := members[string(item.Key)]
			if w.Kind == "member" && (!exists || !bytes.Equal(value, item.Value)) {
				t.Fatalf("not a member: %s", w.ID)
			}
			if w.Kind == "absent" && (exists || len(item.Value) != 0) {
				t.Fatalf("not absent: %s", w.ID)
			}
			if !smt.VerifyProof(item.Proof, cp.Root, item.Key, item.Value, sha256.New()) {
				t.Fatalf("upstream proof rejected: %s", w.ID)
			}
		}
	}
}

func TestWorkloadDistinctNestedAndFixedPrefixes(t *testing.T) {
	ws, _ := loadWorkloadFixture(t)
	groups := map[string]map[int]Bundle{}
	for _, w := range ws {
		seen := map[string]bool{}
		prefix := []byte{0, 5, 10}[w.Batch]
		for _, item := range w.Bundle.Items {
			if seen[string(item.Key)] {
				t.Fatalf("duplicate query: %s", w.ID)
			}
			seen[string(item.Key)] = true
			path := sha256.Sum256(item.Key)
			if w.Pattern == "clustered" && path[0]>>4 != prefix {
				t.Fatalf("wrong actual-path prefix: %s", w.ID)
			}
		}
		group := fmt.Sprintf("%s/%s/%d", w.Kind, w.Pattern, w.Batch)
		if groups[group] == nil {
			groups[group] = map[int]Bundle{}
		}
		groups[group][w.Q] = w.Bundle
	}
	for group, qs := range groups {
		largest := qs[128]
		for _, q := range []int{1, 8, 32} {
			want := Bundle{Root: largest.Root, Items: largest.Items[:q]}
			if !equalBundle(qs[q], want) {
				t.Fatalf("q=%d is not a nested prefix: %s", q, group)
			}
		}
	}
	for _, kind := range []string{"member", "absent"} {
		a := groups[kind+"/dispersed/0"][128]
		for _, batch := range []int{1, 2} {
			b := groups[fmt.Sprintf("%s/dispersed/%d", kind, batch)][128]
			if equalBundle(a, b) {
				t.Fatalf("batch-specific dispersed order was reused for %s", kind)
			}
		}
	}
}

func TestWorkloadAbsentCandidateBudgetAndDerivation(t *testing.T) {
	ws, cp := loadWorkloadFixture(t)
	if cp.AbsentCandidates != 65536 || cp.AbsentAccepted < 128 || cp.AbsentAccepted > cp.AbsentCandidates {
		t.Fatalf("unexpected candidate accounting: candidates=%d accepted=%d", cp.AbsentCandidates, cp.AbsentAccepted)
	}
	members := map[string]bool{}
	for _, key := range cp.Keys {
		members[string(key)] = true
	}
	eligible := map[string]bool{}
	var counts [16]int
	for i := 0; i < cp.AbsentCandidates; i++ {
		key := sha256.Sum256([]byte(fmt.Sprintf("r4/dev/3407/absent/%d", i)))
		if members[string(key[:])] || eligible[string(key[:])] {
			continue
		}
		eligible[string(key[:])] = true
		path := sha256.Sum256(key[:])
		counts[path[0]>>4]++
	}
	if len(eligible) != cp.AbsentAccepted || counts != cp.AbsentPrefixCounts {
		t.Fatal("absent candidate occupancy/accounting mismatch")
	}
	for _, w := range ws {
		if w.Kind == "absent" {
			for _, item := range w.Bundle.Items {
				if !eligible[string(item.Key)] {
					t.Fatalf("absent key outside registered candidate domain: %s", w.ID)
				}
			}
		}
	}
}

func TestMakeWorkloadsDeterministic(t *testing.T) {
	first, firstCP := loadWorkloadFixture(t)
	second, secondCP, err := MakeWorkloads("dev", 4096)
	if err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(firstCP, secondCP) || len(first) != len(second) {
		t.Fatal("repeated generation changed checkpoint or count")
	}
	a, err := json.Marshal(first)
	if err != nil {
		t.Fatal(err)
	}
	b, err := json.Marshal(second)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(a, b) {
		t.Fatal("repeated generation changed ordered query/proof objects")
	}
}

func TestMakeWorkloadsConfirmationDomain(t *testing.T) {
	_, dev := loadWorkloadFixture(t)
	ws, cp, err := MakeWorkloads("confirm", 4096)
	if err != nil {
		t.Fatal(err)
	}
	if len(ws) != 48 || cp.Domain != "confirm" || bytes.Equal(cp.Root, dev.Root) || bytes.Equal(cp.Keys[0], dev.Keys[0]) {
		t.Fatal("confirmation is not a separate deterministic domain")
	}
	want := sha256.Sum256([]byte("r4/confirm/3407/key/0"))
	if !bytes.Equal(cp.Keys[0], want[:]) {
		t.Fatal("incorrect confirmation key domain")
	}
	for _, w := range ws {
		if w.Domain != "confirm" || !strings.HasPrefix(w.ID, "confirm_") || !verify(w.Bundle) {
			t.Fatalf("invalid confirmation workload: %s", w.ID)
		}
	}
}

func TestMakeWorkloadsRejectsInvalidDomainOrPopulation(t *testing.T) {
	for _, tc := range []struct {
		domain string
		n      int
	}{{"", 4096}, {"other", 4096}, {"dev", 0}, {"dev", -1}, {"dev", 128}} {
		ws, _, err := MakeWorkloads(tc.domain, tc.n)
		if err == nil || len(ws) != 0 {
			t.Fatalf("expected no partial workloads for domain=%q N=%d", tc.domain, tc.n)
		}
		if tc.n == 128 && !strings.Contains(err.Error(), "prefix") {
			t.Fatalf("insufficient fixed prefix not reported: %v", err)
		}
	}
}
