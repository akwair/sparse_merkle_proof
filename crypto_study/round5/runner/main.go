package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	smt "github.com/celestiaorg/smt"
	"math/rand"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

func structure(w Workload, sizes map[string]int) map[string]interface{} {
	b := w.Bundle
	depths, kept, masks := []int{}, []int{}, []int{}
	unique, nonzero := map[string]bool{}, map[string]bool{}
	occurrences, zeros, nonzeroOccurrences := 0, 0, 0
	saving := 0
	for _, it := range b.Items {
		c, e := smt.CompactProof(it.Proof, sha256.New())
		must(e)
		d, k := len(it.Proof.SideNodes), len(c.SideNodes)
		depths = append(depths, d)
		kept = append(kept, k)
		masks = append(masks, len(c.BitMask))
		saving += 32*(d-k) - 2 - len(c.BitMask)
		for _, v := range it.Proof.SideNodes {
			occurrences++
			unique[string(v)] = true
			if bytes.Equal(v, make([]byte, 32)) {
				zeros++
			} else {
				nonzeroOccurrences++
				nonzero[string(v)] = true
			}
		}
	}
	dictSaving := 30*occurrences - 32*len(unique) - 2
	if sizes["ordinary"]-sizes["compact"] != saving || sizes["ordinary"]-sizes["dictionary"] != dictSaving {
		panic("size identity")
	}
	return map[string]interface{}{"domain": w.Domain, "n": w.N, "q": w.Q, "kind": w.Kind, "pattern": w.Pattern, "batch": w.Batch, "cell": w.Cell, "id": w.ID, "depths": depths, "retained": kept, "masks": masks, "occurrences": occurrences, "unique_nodes": len(unique), "zero_occurrences": zeros, "nonzero_occurrences": nonzeroOccurrences, "unique_nonzero_nodes": len(nonzero), "sizes": sizes, "compact_saving": saving, "dictionary_saving": dictSaving}
}

func main() {
	if len(os.Args) != 2 {
		panic("usage: conditional_runner NEW_WORK_DIR")
	}
	work := os.Args[1]
	must(os.Mkdir(work, 0755))
	save(filepath.Join(work, "environment.json"), map[string]interface{}{"clock": clockName, "frequency": timerFrequency, "go": runtime.Version(), "os": runtime.GOOS, "arch": runtime.GOARCH, "cpus": runtime.NumCPU(), "gomaxprocs": runtime.GOMAXPROCS(0), "gogc_env": os.Getenv("GOGC"), "gomemlimit_env": os.Getenv("GOMEMLIMIT"), "gomaxprocs_env": os.Getenv("GOMAXPROCS"), "seed": 3407, "commit": "dba215ccb88452c31d823bf156d8f35406c1dc04"})
	var ws []Workload
	for _, domain := range []string{"dev", "confirm"} {
		for _, n := range []int{4096, 16384} {
			items, checkpoint, e := MakeWorkloads(domain, n)
			must(e)
			ws = append(ws, items...)
			save(filepath.Join(work, fmt.Sprintf("tree_%s_n%d.json", domain, n)), checkpoint)
		}
	}
	if len(ws) != 192 {
		panic("workload count")
	}
	rng := rand.New(rand.NewSource(3407))
	rng.Shuffle(len(ws), func(i, j int) { ws[i], ws[j] = ws[j], ws[i] })
	orderIDs := []string{}
	for _, w := range ws {
		orderIDs = append(orderIDs, w.ID)
	}
	save(filepath.Join(work, "execution_order.json"), orderIDs)
	log, e := os.OpenFile(filepath.Join(work, "log.jsonl"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
	must(e)
	defer log.Close()
	jl := json.NewEncoder(log)
	modeRng := rng
	runner := NewEncoder()
	rows := 0
	var diagnostics []map[string]interface{}
	for wi, w := range ws {
		dir := filepath.Join(work, w.ID)
		must(os.Mkdir(dir, 0755))
		save(filepath.Join(dir, "bundle.json"), w.Bundle)
		wires := map[string][]byte{}
		sizes := map[string]int{}
		reference := NewEncoder()
		for _, m := range studyModes {
			raw, e := reference.Encode(w.Bundle, m)
			must(e)
			decoded, e := decodeStudy(raw, m)
			must(e)
			if !equalBundle(w.Bundle, decoded) || !verify(decoded) {
				panic("reference restoration")
			}
			wires[m] = raw
			sizes[m] = len(raw)
			if strings.HasPrefix(m, "reset-") {
				if !bytes.Equal(raw, wires[strings.TrimPrefix(m, "reset-")]) {
					panic("reset differs")
				}
			} else {
				frame(filepath.Join(dir, m+".wire"), raw)
			}
		}
		diag := structure(w, sizes)
		diagnostics = append(diagnostics, diag)
		save(filepath.Join(dir, "diagnostics.json"), diag)
		for _, m := range studyModes {
			for i := 0; i < 2; i++ {
				raw, e := runner.Encode(w.Bundle, m)
				must(e)
				b, e := decodeStudy(raw, m)
				must(e)
				if !verify(b) {
					panic("warmup")
				}
			}
		}
		for rep := 0; rep < 21; rep++ {
			for order, mi := range modeRng.Perm(len(studyModes)) {
				m := studyModes[mi]
				t0 := timestamp()
				raw, e := runner.Encode(w.Bundle, m)
				t1 := timestamp()
				must(e)
				decoded, e := decodeStudy(raw, m)
				t2 := timestamp()
				must(e)
				ok := verify(decoded)
				t3 := timestamp()
				runtime.KeepAlive(raw)
				runtime.KeepAlive(decoded)
				en, de, ve, total := elapsed(t0, t1), elapsed(t1, t2), elapsed(t2, t3), elapsed(t0, t3)
				if total <= 0 || en+de+ve != total {
					panic("clock validation")
				}
				if !ok || !equalBundle(w.Bundle, decoded) || !bytes.Equal(raw, wires[m]) {
					panic("timed correctness")
				}
				must(jl.Encode(map[string]interface{}{"domain": w.Domain, "n": w.N, "q": w.Q, "kind": w.Kind, "pattern": w.Pattern, "batch": w.Batch, "cell": w.Cell, "id": w.ID, "repeat": rep, "order": order, "mode": m, "bytes": len(raw), "encode_ns": en, "decode_ns": de, "verify_ns": ve, "total_ns": total}))
				rows++
			}
		}
		must(log.Sync())
		fmt.Println("finished", wi+1, len(ws), w.ID)
	}
	save(filepath.Join(work, "diagnostics.json"), diagnostics)
	if rows != 36288 {
		panic("row count")
	}
	must(log.Sync())
	save(filepath.Join(work, "completion.json"), map[string]interface{}{"rows": rows, "bundles": len(ws), "complete": true, "utc": time.Now().UTC().Format(time.RFC3339)})
}
