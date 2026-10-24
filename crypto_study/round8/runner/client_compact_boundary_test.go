package main

import (
	"bytes"
	"context"
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
	"testing"
	"time"
)

func TestClientRejectsCompactPaddingPanicAsIntegrityFailure(t *testing.T) {
	a, id := fixtureArchive(t)
	var raw bytes.Buffer
	raw.Write([]byte{'E', '3', 1, 0})
	raw.Write(make([]byte, 32))
	put16(&raw, 1)
	blob(&raw, make([]byte, 32))
	blob(&raw, []byte{1})
	put16(&raw, 1)
	raw.WriteByte(0x40)
	put16(&raw, 0)
	blob(&raw, nil)
	blob(&raw, nil)
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("X-R8-Replay", "false")
		w.Header().Set("X-R8-Queue-Ns", "0")
		w.Header().Set("X-R8-Proof-Ns", "0")
		w.Header().Set("X-R8-Encode-Ns", "0")
		w.Header().Set("Content-Length", strconv.Itoa(raw.Len()))
		w.Write(raw.Bytes())
	}))
	defer ts.Close()
	c := ClientConfig{URL: ts.URL, CaseID: id, Mode: "compact", Timeout: time.Second}
	bodies, err := clientBodies(c, a)
	if err != nil {
		t.Fatal(err)
	}
	cl, tr := newWorkerClient(time.Second)
	defer tr.CloseIdleConnections()
	row := performClientRequest(context.Background(), cl, c, a, 0, 0, 0, bodies[0], time.Now())
	if row.Success || row.ErrorClass != "integrity" || !row.Completion || !strings.Contains(row.Error, "decoder panic rejected") {
		t.Fatalf("malformed compact must become a retained integrity failure: %+v", row)
	}
}
