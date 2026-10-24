package main

import "fmt"

// Preserve the pinned decoder, but contain its historically documented malformed
// compact-mask panic at the new network boundary. A rejected response is an
// integrity failure, never a successful or silently discarded measurement.
func decodeResponseSafely(wire []byte, mode string) (bundle Bundle, err error) {
	defer func() {
		if recovered := recover(); recovered != nil {
			bundle = Bundle{}
			err = fmt.Errorf("decoder panic rejected: %v", recovered)
		}
	}()
	return decodeStudy(wire, mode)
}
