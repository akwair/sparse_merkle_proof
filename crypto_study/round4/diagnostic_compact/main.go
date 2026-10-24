// This isolated functional diagnostic never invokes a performance runner.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"

	smt "github.com/celestiaorg/smt"
)

type Case struct {
	Name string `json:"name"`
	Depth int `json:"depth"`
	MaskHex string `json:"mask_hex"`
	Retained int `json:"retained_nodes"`
	Panic string `json:"recovered_panic"`
	Error string `json:"error"`
	Restored int `json:"restored_nodes"`
	FirstNodeZero bool `json:"first_node_zero"`
}

func observe(name string, proof smt.SparseCompactMerkleProof) (result Case) {
	result = Case{Name:name,Depth:proof.NumSideNodes,MaskHex:fmt.Sprintf("%x",proof.BitMask),Retained:len(proof.SideNodes)}
	defer func() {
		if p := recover(); p != nil { result.Panic = fmt.Sprint(p) }
	}()
	restored, err := smt.DecompactProof(proof, sha256.New())
	if err != nil { result.Error=err.Error();return }
	result.Restored=len(restored.SideNodes)
	if len(restored.SideNodes)>0 { result.FirstNodeZero=bytes.Equal(restored.SideNodes[0],make([]byte,32)) }
	return
}

func main() {
	malformed:=observe("nonzero-unused-padding-bit",smt.SparseCompactMerkleProof{NumSideNodes:1,BitMask:[]byte{0x01}})
	validMask:=observe("valid-one-placeholder-mask",smt.SparseCompactMerkleProof{NumSideNodes:1,BitMask:[]byte{0x80}})
	tree:=smt.NewSparseMerkleTree(smt.NewSimpleMap(),smt.NewSimpleMap(),sha256.New())
	key:=[]byte("diagnostic/3407/control/key-a")
	value:=[]byte("diagnostic/3407/control/value-a")
	if _,err:=tree.Update(key,value);err!=nil { panic(err) }
	if _,err:=tree.Update([]byte("diagnostic/3407/control/key-b"),[]byte("diagnostic/3407/control/value-b"));err!=nil { panic(err) }
	ordinary,err:=tree.Prove(key);if err!=nil { panic(err) }
	compact,err:=smt.CompactProof(ordinary,sha256.New());if err!=nil { panic(err) }
	native:=observe("native-generated-membership-proof",compact)
	nativeVerified:=smt.VerifyCompactProof(compact,tree.Root(),key,value,sha256.New())
	confirmed:=malformed.Panic!="" && validMask.Panic=="" && validMask.Error=="" && validMask.Restored==1 && validMask.FirstNodeZero && native.Panic=="" && native.Error=="" && nativeVerified
	report:=map[string]interface{}{
		"scope":"isolated local functional parser diagnostic; no performance measurements",
		"upstream_commit":"dba215ccb88452c31d823bf156d8f35406c1dc04",
		"seed_label":3407,
		"cases":[]Case{malformed,validMask,native},
		"native_control_verified":nativeVerified,
		"expected_difference_confirmed":confirmed,
	}
	enc:=json.NewEncoder(os.Stdout);enc.SetIndent("","  ")
	if err:=enc.Encode(report);err!=nil { panic(err) }
	if !confirmed { os.Exit(1) }
}
