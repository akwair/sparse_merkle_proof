package main

import (
	"crypto/sha256"
	"runtime"
	"testing"
)

func TestClockResolvesShortWork(t *testing.T) {
	x := [32]byte{1}
	zeros := 0
	for i := 0; i < 100; i++ {
		a := timestamp()
		for j := 0; j < 20; j++ {
			x = sha256.Sum256(x[:])
		}
		b := timestamp()
		runtime.KeepAlive(x)
		if b <= a {
			zeros++
		}
	}
	if zeros > 0 {
		t.Fatalf("unresolved short work: %d/100", zeros)
	}
}
