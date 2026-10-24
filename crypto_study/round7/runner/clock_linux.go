package main

import "time"

const clockName = "Go monotonic time.Since"
const timerFrequency int64 = 1000000000

// Keep the monotonic component from time.Now; time.Since does not use wall time.
var timerEpoch = time.Now()

func timestamp() int64 {
	return time.Since(timerEpoch).Nanoseconds()
}

func elapsed(a, b int64) int64 {
	return b - a
}
