package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"math"
	"math/rand"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"time"

	smt "github.com/celestiaorg/smt"
)

// This extension has no init function, flags, or mutable package globals.
// The original entry point, generators and codecs remain independent of it.
type ApplicationConfig struct {
	Domain       string `json:"domain"`
	N            int    `json:"n"`
	Q            int    `json:"q"`
	ValueBytes   int    `json:"value_bytes"`
	Distribution string `json:"distribution"`
	Batch        int    `json:"batch"`
}

type ApplicationPlan struct {
	Config         ApplicationConfig `json:"config"`
	ID             string            `json:"id"`
	Cell           string            `json:"cell"`
	RequestSetID   string            `json:"request_set_id"`
	RequestIndexes []int             `json:"request_indexes"`
}

type ApplicationRequestSet struct {
	Domain         string `json:"domain"`
	N              int    `json:"n"`
	Distribution   string `json:"distribution"`
	Batch          int    `json:"batch"`
	RequestSetID   string `json:"request_set_id"`
	RequestIndexes []int  `json:"request_indexes"`
}

type ApplicationCheckpoint struct {
	Domain             string   `json:"domain"`
	N                  int      `json:"n"`
	ValueBytes         int      `json:"value_bytes"`
	Root               []byte   `json:"root"`
	Keys               [][]byte `json:"keys"`
	Values             [][]byte `json:"values"`
	MemberPrefixCounts [16]int  `json:"member_prefix_counts"`
}

// A snapshot exposes no update operation. Its trusted root is a value copy;
// returned bundles/checkpoints also receive detached root and key bytes.
type ApplicationSnapshot struct {
	tree        *smt.SparseMerkleTree
	keys        [][]byte
	trustedRoot [32]byte
}

func (c ApplicationConfig) Validate() error {
	if c.Domain != "dev" && c.Domain != "confirm" {
		return fmt.Errorf("application domain must be dev or confirm")
	}
	if c.N != 4096 && c.N != 16384 {
		return fmt.Errorf("application n must be 4096 or 16384")
	}
	if !applicationQueryCount(c.Q) {
		return fmt.Errorf("application q must be 1, 8, 32 or 128")
	}
	if c.ValueBytes != 32 && c.ValueBytes != 1000 {
		return fmt.Errorf("application value bytes must be 32 or 1000")
	}
	if c.Distribution != "uniform" && c.Distribution != "zipf" {
		return fmt.Errorf("application distribution must be uniform or zipf")
	}
	if c.Batch < 0 || c.Batch > 2 {
		return fmt.Errorf("application batch must be 0, 1 or 2")
	}
	return nil
}

func applicationQueryCount(q int) bool { return q == 1 || q == 8 || q == 32 || q == 128 }

func applicationZipfCDF(n int, theta float64) ([]float64, error) {
	if n <= 0 || theta <= 0 || math.IsNaN(theta) || math.IsInf(theta, 0) {
		return nil, fmt.Errorf("invalid finite Zipf parameters")
	}
	cdf := make([]float64, n)
	sum := 0.0
	for i := range cdf {
		sum += math.Pow(float64(i+1), -theta)
		cdf[i] = sum
	}
	for i := range cdf {
		cdf[i] /= sum
	}
	cdf[n-1] = 1
	return cdf, nil
}

// Binary inverse CDF uses half-open intervals: the first CDF value > u.
func applicationZipfRank(cdf []float64, u float64) int {
	return sort.Search(len(cdf), func(i int) bool { return cdf[i] > u })
}

func applicationSampleRanks(rng *rand.Rand, n int, distribution string, count int) ([]int, error) {
	if rng == nil || n <= 0 || count < 1 || count > 128 {
		return nil, fmt.Errorf("invalid request sampling shape")
	}
	if distribution != "uniform" && distribution != "zipf" {
		return nil, fmt.Errorf("unknown request distribution")
	}
	var cdf []float64
	if distribution == "zipf" {
		var err error
		cdf, err = applicationZipfCDF(n, 0.99)
		if err != nil {
			return nil, err
		}
	}
	out := make([]int, count)
	for i := range out {
		if distribution == "uniform" {
			out[i] = rng.Intn(n)
		} else {
			out[i] = applicationZipfRank(cdf, rng.Float64())
		}
	}
	return out, nil
}

func applicationValue(domain string, index, size int) ([]byte, error) {
	if (domain != "dev" && domain != "confirm") || index < 0 || (size != 32 && size != 1000) {
		return nil, fmt.Errorf("invalid application value parameters")
	}
	value := make([]byte, 0, size+sha256.Size)
	for j := 0; len(value) < size; j++ {
		value = append(value, hash(fmt.Sprintf("r7/%s/3407/value/%d/block/%d", domain, index, j))...)
	}
	return value[:size:size], nil
}

func applicationRequestSets() ([]ApplicationRequestSet, error) {
	rng := rand.New(rand.NewSource(3407))
	sets := make([]ApplicationRequestSet, 0, 24)
	// Registered order: values and q never consume sampling draws.
	for _, domain := range []string{"dev", "confirm"} {
		for _, n := range []int{4096, 16384} {
			for _, distribution := range []string{"uniform", "zipf"} {
				for batch := 0; batch < 3; batch++ {
					indexes, err := applicationSampleRanks(rng, n, distribution, 128)
					if err != nil {
						return nil, err
					}
					sets = append(sets, ApplicationRequestSet{Domain: domain, N: n, Distribution: distribution, Batch: batch, RequestSetID: fmt.Sprintf("%s_n%d_%s_b%d", domain, n, distribution, batch), RequestIndexes: indexes})
				}
			}
		}
	}
	return sets, nil
}

func applicationPlans() ([]ApplicationPlan, error) {
	sets, err := applicationRequestSets()
	if err != nil {
		return nil, err
	}
	return applicationPlansFromSets(sets)
}

func applicationPlansFromSets(sets []ApplicationRequestSet) ([]ApplicationPlan, error) {
	plans := make([]ApplicationPlan, 0, 192)
	for _, set := range sets {
		if len(set.RequestIndexes) != 128 {
			return nil, fmt.Errorf("request set must contain 128 indexes")
		}
		for _, valueBytes := range []int{32, 1000} {
			for _, q := range []int{1, 8, 32, 128} {
				c := ApplicationConfig{Domain: set.Domain, N: set.N, Q: q, ValueBytes: valueBytes, Distribution: set.Distribution, Batch: set.Batch}
				if err := c.Validate(); err != nil {
					return nil, err
				}
				cell := fmt.Sprintf("n%d_q%d_v%d_member_%s", c.N, c.Q, c.ValueBytes, c.Distribution)
				plans = append(plans, ApplicationPlan{Config: c, ID: fmt.Sprintf("%s_%s_b%d", c.Domain, cell, c.Batch), Cell: cell, RequestSetID: set.RequestSetID, RequestIndexes: append([]int(nil), set.RequestIndexes[:q]...)})
			}
		}
	}
	return plans, nil
}

func newApplicationSnapshot(domain string, n, valueBytes int) (*ApplicationSnapshot, ApplicationCheckpoint, error) {
	cp := ApplicationCheckpoint{Domain: domain, N: n, ValueBytes: valueBytes}
	config := ApplicationConfig{Domain: domain, N: n, ValueBytes: valueBytes, Q: 1, Distribution: "uniform"}
	if err := config.Validate(); err != nil {
		return nil, cp, err
	}
	snapshot := &ApplicationSnapshot{tree: smt.NewSparseMerkleTree(smt.NewSimpleMap(), smt.NewSimpleMap(), sha256.New()), keys: make([][]byte, n)}
	cp.Keys, cp.Values = make([][]byte, n), make([][]byte, n)
	seen := make(map[string]bool, n)
	for i := 0; i < n; i++ {
		key := hash(fmt.Sprintf("r7/%s/3407/key/%d", domain, i))
		value, err := applicationValue(domain, i, valueBytes)
		if err != nil {
			return nil, cp, err
		}
		if seen[string(key)] {
			return nil, cp, fmt.Errorf("duplicate application key %d", i)
		}
		seen[string(key)] = true
		if _, err := snapshot.tree.Update(key, value); err != nil {
			return nil, cp, fmt.Errorf("application update %d: %w", i, err)
		}
		snapshot.keys[i] = key
		cp.Keys[i], cp.Values[i] = append([]byte(nil), key...), append([]byte(nil), value...)
		cp.MemberPrefixCounts[workloadPathPrefix(key)]++
	}
	copy(snapshot.trustedRoot[:], snapshot.tree.Root())
	cp.Root = append([]byte(nil), snapshot.trustedRoot[:]...)
	return snapshot, cp, nil
}

// Observe does native Get and Prove for EVERY request in order, including
// duplicates, on every reference, warmup, and timed observation. No result or
// proof cache exists. Tree construction is outside all measurement intervals.
func (s *ApplicationSnapshot) Observe(indexes []int) (Bundle, error) {
	if s == nil || s.tree == nil || !applicationQueryCount(len(indexes)) {
		return Bundle{}, fmt.Errorf("invalid application request count")
	}
	b := Bundle{Root: append([]byte(nil), s.trustedRoot[:]...), Items: make([]Item, len(indexes))}
	for i, rank := range indexes {
		if rank < 0 || rank >= len(s.keys) {
			return Bundle{}, fmt.Errorf("request rank %d out of range", rank)
		}
		key := s.keys[rank]
		value, err := s.tree.Get(key)
		if err != nil {
			return Bundle{}, fmt.Errorf("get query %d: %w", i, err)
		}
		proof, err := s.tree.Prove(key)
		if err != nil {
			return Bundle{}, fmt.Errorf("prove query %d: %w", i, err)
		}
		b.Items[i] = Item{Key: append([]byte(nil), key...), Value: append([]byte(nil), value...), Proof: proof}
	}
	return b, nil
}

func (s *ApplicationSnapshot) boundToRequest(b Bundle, indexes []int) bool {
	if s == nil || !applicationQueryCount(len(indexes)) || len(b.Items) != len(indexes) || !bytes.Equal(b.Root, s.trustedRoot[:]) {
		return false
	}
	for i, rank := range indexes {
		if rank < 0 || rank >= len(s.keys) || !bytes.Equal(b.Items[i].Key, s.keys[rank]) {
			return false
		}
	}
	return true
}

func (s *ApplicationSnapshot) Accept(b Bundle, indexes []int) bool {
	return s.boundToRequest(b, indexes) && verify(b)
}

func (p ApplicationPlan) metadata() map[string]interface{} {
	c := p.Config
	return map[string]interface{}{"domain": c.Domain, "n": c.N, "q": c.Q, "value_bytes": c.ValueBytes, "distribution": c.Distribution, "kind": "member", "pattern": c.Distribution, "batch": c.Batch, "id": p.ID, "cell": p.Cell, "request_set_id": p.RequestSetID}
}

func applicationStructure(p ApplicationPlan, b Bundle, sizes map[string]int) map[string]interface{} {
	c := p.Config
	w := Workload{Domain: c.Domain, N: c.N, Q: c.Q, Batch: c.Batch, Kind: "member", Pattern: c.Distribution, ID: p.ID, Cell: p.Cell, Bundle: b}
	diag := structure(w, sizes)
	diag["value_bytes"], diag["distribution"], diag["request_set_id"] = c.ValueBytes, c.Distribution, p.RequestSetID
	unique := map[string]bool{}
	var prefixes, uniquePrefixes [16]int
	for _, item := range b.Items {
		prefix := workloadPathPrefix(item.Key)
		prefixes[prefix]++
		if !unique[string(item.Key)] {
			unique[string(item.Key)] = true
			uniquePrefixes[prefix]++
		}
	}
	diag["unique_query_count"], diag["request_prefix_counts"], diag["unique_request_prefix_counts"] = len(unique), prefixes, uniquePrefixes
	return diag
}

func runApplication(args []string) {
	if len(args) != 1 || args[0] == "" {
		panic("usage: conditional_runner --application NEW_WORK_DIR")
	}
	work := args[0]
	must(os.Mkdir(work, 0755))
	save(filepath.Join(work, "environment.json"), map[string]interface{}{"experiment": "round7_application", "clock": clockName, "frequency": timerFrequency, "go": runtime.Version(), "os": runtime.GOOS, "arch": runtime.GOARCH, "cpus": runtime.NumCPU(), "gomaxprocs": runtime.GOMAXPROCS(0), "gogc_env": os.Getenv("GOGC"), "gomemlimit_env": os.Getenv("GOMEMLIMIT"), "gomaxprocs_env": os.Getenv("GOMAXPROCS"), "seed": 3407, "commit": "dba215ccb88452c31d823bf156d8f35406c1dc04", "warmups": 2, "repetitions": 21, "expected_rows": 36288, "expected_bundles": 192, "modes": studyModes, "pipeline": "native Get+Prove per request -> encode -> decode -> verify; read-only snapshot"})
	save(filepath.Join(work, "sampling.json"), map[string]interface{}{"seed": 3407, "generator": "Go math/rand.New(rand.NewSource(3407))", "domain_order": []string{"dev", "confirm"}, "n_order": []int{4096, 16384}, "distribution_order": []string{"uniform", "zipf"}, "batch_order": []int{0, 1, 2}, "draws_per_set": 128, "replacement": true, "uniform": "Intn(N), rank index 0..N-1", "zipf": "sum pow(k,-0.99) for k=1..N ascending; normalize prefix sums; last CDF=1; first CDF > Float64() by binary search; index 0..N-1", "theta": 0.99, "value_order": []int{32, 1000}, "q_order": []int{1, 8, 32, 128}, "pairing": "request sets generated once independently of value size; q is an ordered prefix; no deduplication or SHA-prefix selection", "key": "SHA256(r7/{domain}/3407/key/{index})", "value": "concatenate SHA256(r7/{domain}/3407/value/{index}/block/{block}), block from 0; truncate to value_bytes", "execution_rng": "independent rand.New(rand.NewSource(3407)); Shuffle bundles then consecutive Perm(9) for each repetition; warmups consume no draws"})
	sets, err := applicationRequestSets()
	must(err)
	save(filepath.Join(work, "request_sets.json"), sets)
	plans, err := applicationPlansFromSets(sets)
	must(err)
	if len(plans) != 192 || len(studyModes) != 9 {
		panic("application matrix count")
	}
	snapshots := map[string]*ApplicationSnapshot{}
	for _, domain := range []string{"dev", "confirm"} {
		for _, n := range []int{4096, 16384} {
			for _, valueBytes := range []int{32, 1000} {
				snapshot, checkpoint, err := newApplicationSnapshot(domain, n, valueBytes)
				must(err)
				key := fmt.Sprintf("%s_n%d_v%d", domain, n, valueBytes)
				snapshots[key] = snapshot
				save(filepath.Join(work, "tree_"+key+".json"), checkpoint)
			}
		}
	}
	rng := rand.New(rand.NewSource(3407))
	rng.Shuffle(len(plans), func(i, j int) { plans[i], plans[j] = plans[j], plans[i] })
	ids := make([]string, len(plans))
	for i, p := range plans {
		ids[i] = p.ID
	}
	save(filepath.Join(work, "execution_order.json"), ids)
	log, err := os.OpenFile(filepath.Join(work, "log.jsonl"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
	must(err)
	defer log.Close()
	jl := json.NewEncoder(log)
	// Exactly one Encoder per application process, including preparation and
	// warmups. The existing reset branches retain their writer lifecycle.
	runner := NewEncoder()
	rows := 0
	diagnostics := make([]map[string]interface{}, 0, len(plans))
	modeOrders := make([]map[string]interface{}, 0, len(plans)*21)
	for wi, p := range plans {
		c := p.Config
		snapshot := snapshots[fmt.Sprintf("%s_n%d_v%d", c.Domain, c.N, c.ValueBytes)]
		dir := filepath.Join(work, p.ID)
		must(os.Mkdir(dir, 0755))
		requests := p.metadata()
		requests["request_indexes"] = p.RequestIndexes
		save(filepath.Join(dir, "requests.json"), requests)
		reference, err := snapshot.Observe(p.RequestIndexes)
		must(err)
		if !snapshot.Accept(reference, p.RequestIndexes) {
			panic("application native reference rejected")
		}
		save(filepath.Join(dir, "bundle.json"), reference)
		wires, sizes := map[string][]byte{}, map[string]int{}
		for _, mode := range studyModes {
			raw, err := runner.Encode(reference, mode)
			must(err)
			restored, err := decodeStudy(raw, mode)
			must(err)
			if !equalBundle(reference, restored) || !snapshot.Accept(restored, p.RequestIndexes) {
				panic("application reference restoration")
			}
			wires[mode], sizes[mode] = raw, len(raw)
			if strings.HasPrefix(mode, "reset-") {
				if !bytes.Equal(raw, wires[strings.TrimPrefix(mode, "reset-")]) {
					panic("application reset differs")
				}
			} else {
				frame(filepath.Join(dir, mode+".wire"), raw)
			}
		}
		diag := applicationStructure(p, reference, sizes)
		diagnostics = append(diagnostics, diag)
		save(filepath.Join(dir, "diagnostics.json"), diag)
		for _, mode := range studyModes {
			for warmup := 0; warmup < 2; warmup++ {
				observed, err := snapshot.Observe(p.RequestIndexes)
				must(err)
				raw, err := runner.Encode(observed, mode)
				must(err)
				restored, err := decodeStudy(raw, mode)
				must(err)
				if !equalBundle(reference, observed) || !equalBundle(reference, restored) || !bytes.Equal(raw, wires[mode]) || !snapshot.Accept(restored, p.RequestIndexes) {
					panic("application warmup correctness")
				}
				runtime.KeepAlive(observed)
				runtime.KeepAlive(raw)
				runtime.KeepAlive(restored)
			}
		}
		for rep := 0; rep < 21; rep++ {
			permutation := rng.Perm(len(studyModes))
			modeOrder := make([]string, len(permutation))
			for order, mi := range permutation {
				modeOrder[order] = studyModes[mi]
			}
			modeOrders = append(modeOrders, map[string]interface{}{"id": p.ID, "repeat": rep, "modes": modeOrder})
			for order, mode := range modeOrder {
				t0 := timestamp()
				observed, proofErr := snapshot.Observe(p.RequestIndexes)
				t1 := timestamp()
				must(proofErr)
				raw, encodeErr := runner.Encode(observed, mode)
				t2 := timestamp()
				must(encodeErr)
				restored, decodeErr := decodeStudy(raw, mode)
				t3 := timestamp()
				must(decodeErr)
				ok := verify(restored)
				t4 := timestamp()
				runtime.KeepAlive(observed)
				runtime.KeepAlive(raw)
				runtime.KeepAlive(restored)
				proofNS, encodeNS, decodeNS, verifyNS := elapsed(t0, t1), elapsed(t1, t2), elapsed(t2, t3), elapsed(t3, t4)
				totalNS, codecNS := proofNS+encodeNS+decodeNS+verifyNS, encodeNS+decodeNS+verifyNS
				if totalNS <= 0 || proofNS < 0 || encodeNS < 0 || decodeNS < 0 || verifyNS < 0 {
					panic("application clock validation")
				}
				if !ok || !snapshot.boundToRequest(restored, p.RequestIndexes) || !equalBundle(reference, observed) || !equalBundle(reference, restored) || !bytes.Equal(raw, wires[mode]) {
					panic("application timed correctness")
				}
				row := p.metadata()
				row["repeat"], row["order"], row["mode"], row["bytes"] = rep, order, mode, len(raw)
				row["proof_ns"], row["encode_ns"], row["decode_ns"], row["verify_ns"] = proofNS, encodeNS, decodeNS, verifyNS
				row["total_ns"], row["codec_total_ns"] = totalNS, codecNS
				must(jl.Encode(row))
				rows++
			}
		}
		must(log.Sync())
		fmt.Println("application finished", wi+1, len(plans), p.ID)
	}
	save(filepath.Join(work, "diagnostics.json"), diagnostics)
	save(filepath.Join(work, "mode_execution_order.json"), modeOrders)
	if rows != 36288 {
		panic("application row count")
	}
	must(log.Sync())
	save(filepath.Join(work, "completion.json"), map[string]interface{}{"rows": rows, "expected_rows": 36288, "bundles": len(plans), "expected_bundles": 192, "warmups": 2, "repetitions": 21, "modes": len(studyModes), "complete": true, "utc": time.Now().UTC().Format(time.RFC3339)})
}
