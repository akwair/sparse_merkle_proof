package main

import "time"

var clockEpoch = time.Now()

const timerFrequency = int64(1_000_000_000)

func timestamp() int64               { return time.Since(clockEpoch).Nanoseconds() }
func elapsed(start, end int64) int64 { return end - start }
