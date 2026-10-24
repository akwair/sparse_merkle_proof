from dataclasses import replace
import hashlib
from pathlib import Path
import pytest
import binary_transport as b

MODES = ('binary-full','binary-bitmap','binary-zlib','binary-bitmap-zlib')

def sample():
    p=b.host.Publisher([b'a',b'b'],session='测试-é')
    return p,p.apply([('remove',b'a'),('add',b'c')])

def test_default_unchanged():
    _,x=sample()
    assert b.encode_batch(x)==b.host.serialized_batch(x)
    assert b.decode_batch(b.encode_batch(x))==x
    assert hashlib.sha256(Path(b.host.__file__).read_bytes()).hexdigest()=='2cc62eb177fab43ef4dd387ec719d5aff9dae4c24e00d6ea87a49efc6d23d3ba'

@pytest.mark.parametrize('mode',MODES)
def test_roundtrip_and_verifier(mode):
    p,x=sample(); w=b.encode_batch(x,mode)
    y=b.decode_batch(w,mode)
    assert x==y
    assert b.host.payload(x)==b.host.payload(y)
    v=b.host.Verifier(p.public_key,x.previous); v.accept(y)
    assert v.checkpoint==x.next
    with pytest.raises(b.host.Rejected): v.accept(y)

@pytest.mark.parametrize('mode',MODES)
def test_reject_corrupt_signature(mode):
    p,x=sample(); x=replace(x,signature=b'\0'*64)
    y=b.decode_batch(b.encode_batch(x,mode),mode)
    with pytest.raises(b.host.Rejected): b.host.Verifier(p.public_key,x.previous).accept(y)

@pytest.mark.parametrize('mode',MODES)
def test_truncation_trailing_and_wrong_mode(mode):
    _,x=sample(); w=b.encode_batch(x,mode)
    for bad in (w[:0],w[:5],w[:-1],w+b'x'):
        with pytest.raises(b.WireError): b.decode_batch(bad,mode)
    other=next(m for m in MODES if m!=mode)
    with pytest.raises(b.WireError): b.decode_batch(w,other)

@pytest.mark.parametrize('mode',MODES)
def test_limits_and_edge_keys(mode):
    p=b.host.Publisher(session='x'*256)
    x=p.apply([('add',b''),('add',b'x'*4096)])
    w=b.encode_batch(x,mode); full=len(b.host.serialized_batch(x))
    assert b.decode_batch(w,mode,b.Limits(max_plain_bytes=full,max_wire_bytes=len(w)))==x
    for lim in (b.Limits(max_plain_bytes=full-1),b.Limits(max_wire_bytes=len(w)-1),b.Limits(max_steps=1),b.Limits(max_key_bytes=4095)):
        with pytest.raises(b.WireError): b.decode_batch(w,mode,lim)

def test_size_identity_and_dense_boundary():
    _,x=sample()
    k=sum(sum(v!=b.host.DEFAULTS[i] for i,v in enumerate(s.siblings)) for s in x.steps)
    a=b.encode_batch(x,'binary-full'); c=b.encode_batch(x,'binary-bitmap')
    assert len(a)-len(c)==32*(256*len(x.steps)-k-len(x.steps))
    for retained in (0,1,255,256):
        siblings=tuple(hashlib.sha256(str(i).encode()).digest() if i<retained else b.host.DEFAULTS[i] for i in range(256))
        y=replace(x,steps=(replace(x.steps[0],siblings=siblings),))
        assert b.decode_batch(b.encode_batch(y,'binary-bitmap'),'binary-bitmap')==y
        assert len(b.encode_batch(y,'binary-full'))-len(b.encode_batch(y,'binary-bitmap'))==32*(255-retained)

def test_explicit_default_and_decompression_bomb():
    _,x=sample()
    # Encoder must not accept malformed source path lengths.
    y=replace(x,steps=(replace(x.steps[0],siblings=(b'x'*32,)),))
    with pytest.raises(b.WireError): b.encode_batch(y,'binary-bitmap')
    import zlib
    with pytest.raises(b.WireError): b.decode_batch(b'R3ZF\0'+zlib.compress(b'x'*10000),'binary-zlib',b.Limits(max_plain_bytes=10))

def test_new_modes_exist():
    assert set(MODES).issubset(b.MODES)
