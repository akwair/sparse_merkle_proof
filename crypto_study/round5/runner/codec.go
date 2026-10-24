package main

import (
	"bytes"
	"compress/zlib"
	"crypto/sha256"
	"fmt"
	"io"

	smt "github.com/celestiaorg/smt"
)

var studyModes = []string{"ordinary", "compact", "dictionary", "zlib-ordinary", "zlib-compact", "zlib-dictionary", "reset-zlib-ordinary", "reset-zlib-compact", "reset-zlib-dictionary"}

// Encoder is sequential-use only. Retained writers have separate histories;
// every frame resets its writer, while buffers and readers are always fresh.
type Encoder struct {
	ordinaryWriter   *zlib.Writer
	compactWriter    *zlib.Writer
	dictionaryWriter *zlib.Writer
}

func NewEncoder() *Encoder { return &Encoder{} }

func (e *Encoder) Encode(b Bundle, mode string) ([]byte, error) {
	if mode == "" {
		mode = "ordinary"
	}
	switch mode {
	case "ordinary", "compact", "zlib-ordinary", "zlib-compact":
		return encode(b, mode)
	case "dictionary":
		return encodeDictionary(b, false, nil)
	case "zlib-dictionary":
		return encodeDictionary(b, true, nil)
	case "reset-zlib-ordinary":
		return encodeReset(b, "zlib-ordinary", &e.ordinaryWriter)
	case "reset-zlib-compact":
		return encodeReset(b, "zlib-compact", &e.compactWriter)
	case "reset-zlib-dictionary":
		return encodeDictionary(b, true, &e.dictionaryWriter)
	default:
		return nil, fmt.Errorf("mode")
	}
}

func decodeStudy(w []byte, mode string) (Bundle, error) {
	if mode == "" {
		mode = "ordinary"
	}
	switch mode {
	case "ordinary", "compact", "zlib-ordinary", "zlib-compact":
		return decode(w, mode)
	case "reset-zlib-ordinary":
		return decode(w, "zlib-ordinary")
	case "reset-zlib-compact":
		return decode(w, "zlib-compact")
	case "dictionary":
		return decodeDictionary(w, false)
	case "zlib-dictionary", "reset-zlib-dictionary":
		return decodeDictionary(w, true)
	default:
		return Bundle{}, fmt.Errorf("mode")
	}
}

// encodeReset copies the legacy encode path. Only writer construction changes:
// no intermediate ordinary frame, extra serialization, or buffer reuse occurs.
func encodeReset(b Bundle, m string, retained **zlib.Writer) ([]byte, error) {
	idx, e := modeIndex(m)
	if e != nil {
		return nil, e
	}
	if len(b.Root) != 32 || len(b.Items) < 1 || len(b.Items) > 256 {
		return nil, fmt.Errorf("bundle shape")
	}
	var out bytes.Buffer
	out.Write(b.Root)
	put16(&out, len(b.Items))
	for _, it := range b.Items {
		if len(it.Key) > 4096 || len(it.Value) > 4096 {
			return nil, fmt.Errorf("field limit")
		}
		blob(&out, it.Key)
		blob(&out, it.Value)
		p := it.Proof
		nodes := p.SideNodes
		if compactMode(m) {
			c, e := smt.CompactProof(p, sha256.New())
			if e != nil {
				return nil, e
			}
			put16(&out, c.NumSideNodes)
			out.Write(c.BitMask)
			nodes = c.SideNodes
		}
		if len(nodes) > 256 {
			return nil, fmt.Errorf("depth")
		}
		put16(&out, len(nodes))
		for _, v := range nodes {
			if len(v) != 32 {
				return nil, fmt.Errorf("node size")
			}
			out.Write(v)
		}
		blob(&out, p.NonMembershipLeafData)
		blob(&out, p.SiblingData)
	}
	raw := out.Bytes()
	if idx >= 2 {
		var z bytes.Buffer
		w := *retained
		if w == nil {
			w, e = zlib.NewWriterLevel(&z, 6)
			if e != nil {
				return nil, e
			}
			*retained = w
		}
		w.Reset(&z)
		if _, e = w.Write(raw); e != nil {
			return nil, e
		}
		if e = w.Close(); e != nil {
			return nil, e
		}
		raw = z.Bytes()
	}
	return append([]byte{'E', '3', byte(idx), 0}, raw...), nil
}

// dictionaryBody uses deterministic first-occurrence order. Dictionary entries
// contain all side-node byte values, including the zero placeholder if present.
func dictionaryBody(b Bundle) ([]byte, error) {
	if len(b.Root) != 32 || len(b.Items) < 1 || len(b.Items) > 256 {
		return nil, fmt.Errorf("bundle shape")
	}
	indices := make(map[[32]byte]uint16)
	var dictionary [][]byte
	for _, it := range b.Items {
		if len(it.Key) > 4096 || len(it.Value) > 4096 || len(it.Proof.NonMembershipLeafData) > 65 || len(it.Proof.SiblingData) > 65 {
			return nil, fmt.Errorf("field limit")
		}
		if len(it.Proof.SideNodes) > 256 {
			return nil, fmt.Errorf("depth")
		}
		for _, node := range it.Proof.SideNodes {
			if len(node) != 32 {
				return nil, fmt.Errorf("node size")
			}
			var key [32]byte
			copy(key[:], node)
			if _, exists := indices[key]; !exists {
				if len(dictionary) == 65535 {
					return nil, fmt.Errorf("dictionary count")
				}
				indices[key] = uint16(len(dictionary))
				dictionary = append(dictionary, node)
			}
		}
	}
	var out bytes.Buffer
	put16(&out, len(dictionary))
	for _, node := range dictionary {
		out.Write(node)
	}
	out.Write(b.Root)
	put16(&out, len(b.Items))
	for _, it := range b.Items {
		blob(&out, it.Key)
		blob(&out, it.Value)
		put16(&out, len(it.Proof.SideNodes))
		for _, node := range it.Proof.SideNodes {
			var key [32]byte
			copy(key[:], node)
			put16(&out, int(indices[key]))
		}
		blob(&out, it.Proof.NonMembershipLeafData)
		blob(&out, it.Proof.SiblingData)
	}
	if out.Len() > maxWire-4 {
		return nil, fmt.Errorf("payload limit")
	}
	return out.Bytes(), nil
}

func encodeDictionary(b Bundle, compressed bool, retained **zlib.Writer) ([]byte, error) {
	raw, err := dictionaryBody(b)
	if err != nil {
		return nil, err
	}
	idx := byte(0)
	if compressed {
		idx = 1
		var z bytes.Buffer
		var w *zlib.Writer
		if retained == nil {
			w, err = zlib.NewWriterLevel(&z, 6)
		} else {
			w = *retained
			if w == nil {
				w, err = zlib.NewWriterLevel(&z, 6)
				*retained = w
			}
			if err == nil {
				w.Reset(&z)
			}
		}
		if err != nil {
			return nil, err
		}
		if _, err = w.Write(raw); err != nil {
			return nil, err
		}
		if err = w.Close(); err != nil {
			return nil, err
		}
		raw = z.Bytes()
	}
	if len(raw) > maxWire-4 {
		return nil, fmt.Errorf("wire limit")
	}
	return append([]byte{'D', '4', idx, 0}, raw...), nil
}

func decodeDictionary(w []byte, compressed bool) (Bundle, error) {
	var b Bundle
	idx := byte(0)
	if compressed {
		idx = 1
	}
	if len(w) < 4 || len(w) > maxWire || !bytes.Equal(w[:4], []byte{'D', '4', idx, 0}) {
		return b, fmt.Errorf("envelope")
	}
	raw := w[4:]
	if compressed {
		src := bytes.NewReader(raw)
		z, err := zlib.NewReader(src)
		if err != nil {
			return b, err
		}
		decoded, err := io.ReadAll(io.LimitReader(z, maxWire+1))
		closeErr := z.Close()
		if err != nil || closeErr != nil || len(decoded) > maxWire || src.Len() != 0 {
			return b, fmt.Errorf("inflate/trailing")
		}
		raw = decoded
	}
	r := reader{b: raw}
	u, err := r.n16()
	if err != nil {
		return b, err
	}
	packed, err := r.take(32 * u)
	if err != nil {
		return b, err
	}
	dictionary := make([][]byte, u)
	for i := range dictionary {
		dictionary[i] = packed[32*i : 32*(i+1)]
	}
	b.Root, err = r.take(32)
	if err != nil {
		return b, err
	}
	n, err := r.n16()
	if err != nil || n < 1 || n > 256 {
		return b, fmt.Errorf("count")
	}
	for i := 0; i < n; i++ {
		var it Item
		it.Key, err = r.blob(4096)
		if err != nil {
			return b, err
		}
		it.Value, err = r.blob(4096)
		if err != nil {
			return b, err
		}
		k, err := r.n16()
		if err != nil || k > 256 {
			return b, fmt.Errorf("nodes")
		}
		for j := 0; j < k; j++ {
			position, err := r.n16()
			if err != nil || position >= u {
				return b, fmt.Errorf("dictionary index")
			}
			it.Proof.SideNodes = append(it.Proof.SideNodes, dictionary[position])
		}
		it.Proof.NonMembershipLeafData, err = r.blob(65)
		if err != nil {
			return b, err
		}
		it.Proof.SiblingData, err = r.blob(65)
		if err != nil {
			return b, err
		}
		b.Items = append(b.Items, it)
	}
	if r.p != len(raw) {
		return b, fmt.Errorf("trailing")
	}
	return b, nil
}
