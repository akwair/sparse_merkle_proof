"""Optional canonical binary adapters for the unchanged Round2 signed object.

Not a new cryptographic construction. Default/legacy modes delegate unchanged.
All integers are unsigned big endian. Every binary variant preserves all fields.
"""
import sys
from pathlib import Path
import struct
import zlib
sys.path.insert(0,str(Path(__file__).resolve().parent/'frozen'))
import proof_transport as old
from proof_transport import host, Limits, WireError
MAGIC = {'binary-full':b'R3BF\0','binary-bitmap':b'R3BC\0',
         'binary-zlib':b'R3ZF\0','binary-bitmap-zlib':b'R3ZC\0'}
MODES = old.MODES + tuple(MAGIC)

def _checkpoint_bytes(c):
    session=c.session.encode('utf-8')
    if not 1<=len(c.session)<=256 or len(c.root)!=32:
        raise WireError('checkpoint shape')
    return struct.pack('>H',len(session))+session+struct.pack('>QQ',c.epoch,c.size)+c.root

def _binary(batch,compact):
    if not 1<=len(batch.steps)<=256 or len(batch.signature)!=64:
        raise WireError('batch shape')
    parts=[_checkpoint_bytes(batch.previous),_checkpoint_bytes(batch.next),struct.pack('>H',len(batch.steps))]
    for s in batch.steps:
        if s.operation not in ('add','remove') or len(s.key)>4096 or len(s.siblings)!=256 or any(type(v)is not bytes or len(v)!=32 for v in s.siblings):
            raise WireError('step shape')
        parts.extend((bytes([s.operation=='remove']),struct.pack('>H',len(s.key)),s.key))
        if compact:
            mask=0; nodes=[]
            for i,v in enumerate(s.siblings):
                if v!=host.DEFAULTS[i]: mask|=1<<i; nodes.append(v)
            parts.extend((mask.to_bytes(32,'big'),b''.join(nodes)))
        else: parts.append(b''.join(s.siblings))
    parts.append(batch.signature)
    return b''.join(parts)

def encode_batch(batch,mode='full'):
    if mode in old.MODES: return old.encode_batch(batch,mode)
    if mode not in MAGIC: raise WireError('unknown mode')
    try:
        raw=_binary(batch,mode in ('binary-bitmap','binary-bitmap-zlib'))
        if mode in ('binary-zlib','binary-bitmap-zlib'): raw=zlib.compress(raw,6)
        return MAGIC[mode]+raw
    except (ValueError,OverflowError,struct.error,UnicodeError) as e:
        raise WireError('invalid source') from e

class Reader:
    def __init__(self,raw): self.raw=raw; self.pos=0
    def take(self,n):
        if n<0 or self.pos+n>len(self.raw): raise WireError('truncated binary')
        v=self.raw[self.pos:self.pos+n]; self.pos+=n; return v
    def integer(self,n): return int.from_bytes(self.take(n),'big')
    def checkpoint(self):
        n=self.integer(2)
        if n>1024: raise WireError('session limit')
        s=self.take(n).decode('utf-8')
        if not 1<=len(s)<=256: raise WireError('session length')
        epoch=self.integer(8); size=self.integer(8)
        return host.Checkpoint(s,epoch,self.take(32),size)

def decode_batch(wire,mode='full',limits=Limits()):
    if mode in old.MODES: return old.decode_batch(wire,mode,limits)
    if mode not in MAGIC: raise WireError('unknown mode')
    try:
        if type(wire)is not bytes or len(wire)>limits.max_wire_bytes or not wire.startswith(MAGIC[mode]):
            raise WireError('wire envelope/limit')
        raw=wire[5:]
        if mode in ('binary-zlib','binary-bitmap-zlib'):
            d=zlib.decompressobj(); raw=d.decompress(raw,limits.max_plain_bytes+1)
            if len(raw)>limits.max_plain_bytes or not d.eof or d.unused_data or d.unconsumed_tail:
                raise WireError('inflation limit/trailing/truncated stream')
        r=Reader(raw); previous=r.checkpoint(); next_cp=r.checkpoint(); count=r.integer(2)
        if not 1<=count<=min(limits.max_steps,256): raise WireError('step count')
        compact=mode in ('binary-bitmap','binary-bitmap-zlib'); parsed=[]; meta=[]
        for _ in range(count):
            op=r.integer(1)
            if op not in (0,1): raise WireError('operation')
            n=r.integer(2)
            if n>limits.max_key_bytes: raise WireError('key limit')
            key=r.take(n); operation=('add','remove')[op]
            mask=r.integer(32) if compact else (1<<256)-1
            saved=tuple(r.take(32) for _ in range(mask.bit_count()))
            parsed.append((operation,key,mask,saved))
            meta.append({'operation':operation,'key':key.hex(),'siblings':[]})
        signature=r.take(64)
        if r.pos!=len(raw): raise WireError('trailing data')
        body={'domain':host.DOMAIN.decode('ascii'),'previous':host.checkpoint_dict(previous),
              'next':host.checkpoint_dict(next_cp),'steps':meta,'signature':signature.hex()}
        restored=len(old._canonical(body))+count*(old._hex_array_size(256)-2)
        if restored>limits.max_plain_bytes: raise WireError('restored full JSON limit')
        steps=[]
        for operation,key,mask,saved in parsed:
            if compact:
                nodes=list(host.DEFAULTS[:256]); pos=0
                for i in range(256):
                    if mask & (1<<i):
                        v=saved[pos]; pos+=1
                        if v==host.DEFAULTS[i]: raise WireError('noncanonical explicit default')
                        nodes[i]=v
                siblings=tuple(nodes)
            else: siblings=saved
            steps.append(host.Step(operation,key,siblings))
        return host.Batch(previous,next_cp,tuple(steps),signature)
    except WireError: raise
    except (ValueError,TypeError,UnicodeError,OverflowError,zlib.error) as e:
        raise WireError('invalid binary') from e
