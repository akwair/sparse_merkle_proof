package main

import (
	"crypto/sha256"
	"math"
	"runtime"
	"testing"
)

func TestClockLinuxNanosecondArithmetic(t *testing.T) {
	if timerFrequency != 1000000000 {
		t.Fatalf("nanosecond clock frequency = %d", timerFrequency)
	}
	if clockName != "Go monotonic time.Since" {
		t.Fatalf("unexpected clock label: %q", clockName)
	}
	for _, tc := range []struct {
		name string
		a, b int64
		want int64
	}{
		{"zero", 123, 123, 0},
		{"one nanosecond", 123, 124, 1},
		{"second boundary", 999999999, 1000000001, 2},
		{"multiple seconds", 1500000001, 4500000008, 3000000007},
		{"large timestamp", math.MaxInt64 - 101, math.MaxInt64 - 1, 100},
	} {
		t.Run(tc.name, func(t *testing.T) {
			if got := elapsed(tc.a, tc.b); got != tc.want {
				t.Fatalf("elapsed(%d, %d) = %d, want %d", tc.a, tc.b, got, tc.want)
			}
		})
	}
}

func TestClockLinuxStageSum(t *testing.T) {
	for _, ticks := range [][4]int64{
		{0, 1, 2, 3},
		{100, 100, 101, 105},
		{999999999, 1000000001, 1000000004, 2000000009},
		{math.MaxInt64 - 19, math.MaxInt64 - 17, math.MaxInt64 - 8, math.MaxInt64 - 1},
	} {
		encode := elapsed(ticks[0], ticks[1])
		decode := elapsed(ticks[1], ticks[2])
		verify := elapsed(ticks[2], ticks[3])
		total := elapsed(ticks[0], ticks[3])
		if total <= 0 || encode < 0 || decode < 0 || verify < 0 || encode+decode+verify != total {
			t.Fatalf("invalid stage sum for %v: %d + %d + %d != %d", ticks, encode, decode, verify, total)
		}
	}
}

func TestClockLinuxMonotonicStages(t *testing.T) {
	previous := timestamp()
	if previous < 0 {
		t.Fatalf("negative epoch-relative timestamp: %d", previous)
	}
	for i := 0; i < 10000; i++ {
		now := timestamp()
		if now < previous {
			t.Fatalf("clock moved backwards at read %d: %d -> %d", i, previous, now)
		}
		previous = now
	}
	x := [32]byte{1}
	for i := 0; i < 100; i++ {
		var ticks [4]int64
		ticks[0] = timestamp()
		for stage := 1; stage <= 3; stage++ {
			for j := 0; j < 20; j++ {
				x = sha256.Sum256(x[:])
			}
			ticks[stage] = timestamp()
			if ticks[stage] <= ticks[stage-1] {
				t.Fatalf("short stage unresolved at repetition %d stage %d: %v", i, stage, ticks)
			}
		}
		runtime.KeepAlive(x)
		stageSum := elapsed(ticks[0], ticks[1]) + elapsed(ticks[1], ticks[2]) + elapsed(ticks[2], ticks[3])
		if total := elapsed(ticks[0], ticks[3]); total <= 0 || stageSum != total {
			t.Fatalf("measured stage sum = %d, total = %d", stageSum, total)
		}
	}
}
