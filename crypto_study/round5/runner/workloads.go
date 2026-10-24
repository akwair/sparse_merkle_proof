package main

import (
	"bytes"
	"crypto/sha256"
	"fmt"
	"sort"

	smt "github.com/celestiaorg/smt"
)

// Workload is one ordered, same-root query bundle from the frozen matrix.
type Workload struct {
	Domain                  string
	N, Q, Batch             int
	Kind, Pattern, ID, Cell string
	Bundle                  Bundle
}

// TreeCheckpoint contains the complete inputs needed to rebuild one tree.
type TreeCheckpoint struct {
	Domain                                 string
	N                                      int
	Root                                   []byte
	Keys, Values                           [][]byte
	AbsentCandidates, AbsentAccepted       int
	MemberPrefixCounts, AbsentPrefixCounts [16]int
}

const workloadAbsentCandidateCap = 65536

type workloadCandidate struct {
	key, value []byte
	prefix     byte
}

// MakeWorkloads builds one tree and returns the 48 preregistered bundles.
// It performs no measurements. The full absent-candidate budget is scanned,
// rather than stopping when a chosen prefix happens to contain enough keys.
// The returned checkpoint records the resulting candidate occupancy.
func MakeWorkloads(domain string, n int) ([]Workload, TreeCheckpoint, error) {
	cp := TreeCheckpoint{Domain: domain, N: n}
	if domain != "dev" && domain != "confirm" {
		return nil, cp, fmt.Errorf("workload domain must be dev or confirm")
	}
	if n <= 0 {
		return nil, cp, fmt.Errorf("workload population must be positive")
	}
	tree := smt.NewSparseMerkleTree(smt.NewSimpleMap(), smt.NewSimpleMap(), sha256.New())
	cp.Keys = make([][]byte, n)
	cp.Values = make([][]byte, n)
	members := make([]workloadCandidate, 0, n)
	memberSet := make(map[string]bool, n)
	for i := 0; i < n; i++ {
		key := hash(fmt.Sprintf("r4/%s/3407/key/%d", domain, i))
		value := hash(fmt.Sprintf("r4/%s/3407/value/%d", domain, i))
		if memberSet[string(key)] {
			return nil, cp, fmt.Errorf("duplicate member key at candidate %d", i)
		}
		memberSet[string(key)] = true
		if _, err := tree.Update(key, value); err != nil {
			return nil, cp, fmt.Errorf("tree update %d: %w", i, err)
		}
		cp.Keys[i], cp.Values[i] = key, value
		prefix := workloadPathPrefix(key)
		cp.MemberPrefixCounts[prefix]++
		members = append(members, workloadCandidate{key: key, value: value, prefix: prefix})
	}
	cp.Root = append([]byte(nil), tree.Root()...)
	fixedPrefixes := [3]byte{0, 5, 10}
	for _, prefix := range fixedPrefixes {
		if cp.MemberPrefixCounts[prefix] < 128 {
			return nil, cp, fmt.Errorf("member prefix %x has %d candidates; need 128", prefix, cp.MemberPrefixCounts[prefix])
		}
	}

	absent := make([]workloadCandidate, 0, workloadAbsentCandidateCap)
	absentSet := make(map[string]bool, workloadAbsentCandidateCap)
	for i := 0; i < workloadAbsentCandidateCap; i++ {
		cp.AbsentCandidates++
		key := hash(fmt.Sprintf("r4/%s/3407/absent/%d", domain, i))
		if memberSet[string(key)] || absentSet[string(key)] {
			continue
		}
		exists, err := tree.Has(key)
		if err != nil {
			return nil, cp, fmt.Errorf("check absent candidate %d: %w", i, err)
		}
		if exists {
			return nil, cp, fmt.Errorf("absent candidate %d unexpectedly exists in tree", i)
		}
		absentSet[string(key)] = true
		prefix := workloadPathPrefix(key)
		cp.AbsentPrefixCounts[prefix]++
		absent = append(absent, workloadCandidate{key: key, prefix: prefix})
	}
	cp.AbsentAccepted = len(absent)
	for _, prefix := range fixedPrefixes {
		if cp.AbsentPrefixCounts[prefix] < 128 {
			return nil, cp, fmt.Errorf("absent prefix %x has %d candidates after cap %d; need 128", prefix, cp.AbsentPrefixCounts[prefix], cp.AbsentCandidates)
		}
	}

	workloads := make([]Workload, 0, 48)
	// Proof caching only avoids duplicate preparation work across nested input
	// fixtures. Each returned bundle still contains every query and proof, and
	// the timed consumer must verify every item independently.
	proofs := make(map[string]Item)
	for _, kind := range []string{"member", "absent"} {
		candidates := members
		if kind == "absent" {
			candidates = absent
		}
		for _, pattern := range []string{"dispersed", "clustered"} {
			for batch, prefix := range fixedPrefixes {
				ordered := workloadOrderedCandidates(candidates, domain, n, kind, pattern, batch, prefix)
				if len(ordered) < 128 {
					return nil, cp, fmt.Errorf("%s %s batch %d has fewer than 128 candidates", kind, pattern, batch)
				}
				items := make([]Item, 128)
				for i, candidate := range ordered[:128] {
					item, ok := proofs[string(candidate.key)]
					if !ok {
						proof, err := tree.Prove(candidate.key)
						if err != nil {
							return nil, cp, fmt.Errorf("prove %s candidate: %w", kind, err)
						}
						item = Item{Key: candidate.key, Value: candidate.value, Proof: proof}
						if !smt.VerifyProof(proof, cp.Root, item.Key, item.Value, sha256.New()) {
							return nil, cp, fmt.Errorf("upstream rejected generated %s proof", kind)
						}
						proofs[string(candidate.key)] = item
					}
					items[i] = item
				}
				for _, q := range []int{1, 8, 32, 128} {
					cell := fmt.Sprintf("n%d_q%d_%s_%s", n, q, kind, pattern)
					workloads = append(workloads, Workload{
						Domain: domain, N: n, Q: q, Batch: batch,
						Kind: kind, Pattern: pattern, Cell: cell,
						ID:     fmt.Sprintf("%s_%s_b%d", domain, cell, batch),
						Bundle: Bundle{Root: cp.Root, Items: items[:q:q]},
					})
				}
			}
		}
	}
	return workloads, cp, nil
}

func workloadPathPrefix(key []byte) byte {
	path := sha256.Sum256(key)
	return path[0] >> 4
}

func workloadOrderedCandidates(candidates []workloadCandidate, domain string, n int, kind, pattern string, batch int, prefix byte) []workloadCandidate {
	if pattern == "clustered" {
		// Candidate generation index supplies the fixed within-prefix ordering.
		out := make([]workloadCandidate, 0)
		for _, candidate := range candidates {
			if candidate.prefix == prefix {
				out = append(out, candidate)
			}
		}
		return out
	}
	// SHA256(domain-separated text || raw candidate key) is the permutation
	// rank. Only the registered seed 3407 is used; q is deliberately absent so
	// that every q is a prefix of one fixed batch-specific order. Raw key bytes
	// break a hypothetical rank collision deterministically.
	type ranked struct {
		candidate workloadCandidate
		rank      [32]byte
	}
	salt := []byte(fmt.Sprintf("r4/%s/3407/dispersed/n%d/%s/b%d/", domain, n, kind, batch))
	input := make([]byte, len(salt)+sha256.Size)
	copy(input, salt)
	ranks := make([]ranked, len(candidates))
	for i, candidate := range candidates {
		copy(input[len(salt):], candidate.key)
		ranks[i] = ranked{candidate: candidate, rank: sha256.Sum256(input)}
	}
	sort.Slice(ranks, func(i, j int) bool {
		cmp := bytes.Compare(ranks[i].rank[:], ranks[j].rank[:])
		if cmp == 0 {
			return bytes.Compare(ranks[i].candidate.key, ranks[j].candidate.key) < 0
		}
		return cmp < 0
	})
	out := make([]workloadCandidate, len(ranks))
	for i, candidate := range ranks {
		out[i] = candidate.candidate
	}
	return out
}
