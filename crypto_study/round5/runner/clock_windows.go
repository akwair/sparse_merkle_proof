package main

import (
	"syscall"
	"unsafe"
)

const clockName = "QueryPerformanceCounter"

var timerDLL = syscall.NewLazyDLL("kernel32.dll")
var timerCounter = timerDLL.NewProc("QueryPerformanceCounter")
var timerFrequency = func() int64 {
	var f int64
	ok, _, _ := timerDLL.NewProc("QueryPerformanceFrequency").Call(uintptr(unsafe.Pointer(&f)))
	if ok == 0 || f <= 0 {
		panic("QPC frequency")
	}
	return f
}()

func timestamp() int64 {
	var n int64
	ok, _, _ := timerCounter.Call(uintptr(unsafe.Pointer(&n)))
	if ok == 0 {
		panic("QPC counter")
	}
	return n
}
func elapsed(a, b int64) int64 {
	d := b - a
	return (d/timerFrequency)*1000000000 + (d%timerFrequency)*1000000000/timerFrequency
}
