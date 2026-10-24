package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"
)

func main() {
	if e := run(os.Args[1:]); e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(1)
	}
}
func run(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("usage: round8 serve|client|check [flags]")
	}
	f := flag.NewFlagSet(args[0], flag.ContinueOnError)
	data := f.String("data", "", "archived measurements directory")
	work := f.String("work-dir", "", "new exclusive output directory")
	switch args[0] {
	case "serve":
		listen := f.String("listen", "127.0.0.1:8080", "HTTP/1.1 address")
		workers := f.Int("workers", 8, "fixed worker count")
		replay := f.Bool("replay", false, "diagnostic reference replay; exclude from formal measurements")
		if e := f.Parse(args[1:]); e != nil {
			return e
		}
		if f.NArg() != 0 || *data == "" || *work == "" {
			return fmt.Errorf("serve requires --data and --work-dir")
		}
		if e := os.Mkdir(*work, 0755); e != nil {
			return e
		}
		a, e := LoadArchive(*data, nil)
		if e != nil {
			return e
		}
		s, e := NewService(a, *workers, *replay)
		if e != nil {
			return e
		}
		if e = writeJSON(filepath.Join(*work, "environment.json"), Environment(a)); e != nil {
			return e
		}
		if e = writeJSON(filepath.Join(*work, "config.json"), map[string]any{"data": a.root, "listen": *listen, "workers": *workers, "replay": *replay, "protocol": "HTTP/1.1 JSON keys/raw legacy frame", "encoder_initialization": "one retained encoder perworker; three reset writers primed beforelisten"}); e != nil {
			return e
		}
		ln, e := net.Listen("tcp", *listen)
		if e != nil {
			return e
		}
		srv := &http.Server{Handler: s.Handler(), ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 10 * time.Second, WriteTimeout: 30 * time.Second, IdleTimeout: 90 * time.Second, MaxHeaderBytes: 16 << 10}
		sigCtx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
		defer stop()
		errC := make(chan error, 1)
		go func() { errC <- srv.Serve(ln) }()
		fmt.Println("ready", ln.Addr().String())
		select {
		case e = <-errC:
			if !errors.Is(e, http.ErrServerClosed) {
				return e
			}
		case <-sigCtx.Done():
			ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
			defer cancel()
			if e = srv.Shutdown(ctx); e != nil {
				srv.Close()
				return e
			}
			if e = <-errC; !errors.Is(e, http.ErrServerClosed) {
				return e
			}
		}
		if e = writeJSON(filepath.Join(*work, "stats.json"), s.Stats()); e != nil {
			return e
		}
		if e = writeJSON(filepath.Join(*work, "final_environment.json"), Environment(a)); e != nil {
			return e
		}
		return writeJSON(filepath.Join(*work, "completion.json"), map[string]any{"complete": true, "shutdown": "graceful", "utc": time.Now().UTC().Format(time.RFC3339Nano)})
	case "client":
		c := ClientConfig{}
		f.StringVar(&c.URL, "url", "", "server base URL")
		f.StringVar(&c.CaseID, "case", "", "registered case without _b suffix")
		f.StringVar(&c.Mode, "mode", "ordinary", "study mode")
		f.IntVar(&c.Concurrency, "concurrency", 1, "closed-loop clients")
		f.DurationVar(&c.Warmup, "warmup", 3*time.Second, "connection/proof warmup")
		f.DurationVar(&c.Duration, "duration", 10*time.Second, "nominal admission window")
		f.DurationVar(&c.Timeout, "timeout", 5*time.Second, "perrequest timeout")
		if e := f.Parse(args[1:]); e != nil {
			return e
		}
		c.Data = *data
		c.WorkDir = *work
		if f.NArg() != 0 || *data == "" || *work == "" || c.URL == "" || c.CaseID == "" || !validMode(c.Mode) || c.Concurrency < 1 || c.Duration <= 0 || c.Warmup < 0 || c.Timeout <= 0 {
			return fmt.Errorf("invalid client arguments")
		}
		if e := os.Mkdir(*work, 0755); e != nil {
			return e
		}
		a, e := LoadClientArchive(*data, []string{c.CaseID})
		if e != nil {
			return e
		}
		return RunClient(c, a)
	case "check":
		if e := f.Parse(args[1:]); e != nil {
			return e
		}
		if f.NArg() != 0 || *data == "" || *work == "" {
			return fmt.Errorf("check requires --data and --work-dir")
		}
		if e := os.Mkdir(*work, 0755); e != nil {
			return e
		}
		a, e := LoadArchive(*data, nil)
		if e != nil {
			return e
		}
		receipt, e := a.Check()
		if e != nil {
			return e
		}
		if e = writeJSON(filepath.Join(*work, "environment.json"), Environment(a)); e != nil {
			return e
		}
		return writeJSON(filepath.Join(*work, "completion.json"), receipt)
	default:
		return fmt.Errorf("unknown command %s", args[0])
	}
}
