"""Post-run independent frame/metric audit; not a timed experiment."""
from pathlib import Path
import base64, hashlib, json, statistics, zlib
from collections import defaultdict
import binary_transport as codec
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

ROOT=Path(__file__).resolve().parent
WORK=ROOT/'runs/screening_001'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def b64(v):return b'' if v is None else base64.b64decode(v)

def parse_external(wire,mode):
    modes=['ordinary','compact','zlib-ordinary','zlib-compact'];mi=modes.index(mode)
    assert wire[:4]==b'E3'+bytes([mi,0])
    raw=wire[4:]
    if mi>=2:
        z=zlib.decompressobj();raw=z.decompress(raw);assert z.eof and not z.unused_data and not z.unconsumed_tail
    pos=0
    def take(n):
        nonlocal pos
        assert pos+n<=len(raw);v=raw[pos:pos+n];pos+=n;return v
    def number():return int.from_bytes(take(2),'big')
    def blob():return take(number())
    root=take(32);items=[]
    for _ in range(number()):
        key=blob();value=blob();compact=mi%2==1
        depth=number() if compact else None
        mask=take((depth+7)//8) if compact else None
        nodes=[take(32) for _ in range(number())]
        nm=blob();sd=blob()
        if compact:
            restored=[];p=0
            for i in range(depth):
                if mask[i//8] & (1<<(7-i%8)):restored.append(bytes(32))
                else:restored.append(nodes[p]);p+=1
            assert p==len(nodes);nodes=restored
        items.append((key,value,nodes,nm,sd))
    assert pos==len(raw)
    return root,items

def verify_external(root,item):
    key,value,nodes,nm,sd=item;path=hashlib.sha256(key).digest()
    if value:
        current=hashlib.sha256(b'\0'+path+hashlib.sha256(value).digest()).digest()
    elif nm:
        if len(nm)!=65 or nm[:1]!=b'\0' or nm[1:33]==path:return False
        current=hashlib.sha256(nm).digest()
    else:current=bytes(32)
    for i,node in enumerate(nodes):
        bit=len(nodes)-1-i
        right=(path[bit//8]>>(7-bit%8))&1
        current=hashlib.sha256(b'\1'+(node+current if right else current+node)).digest()
    return current==root

def main():
    completion=read(WORK/'completion.json');assert completion['complete'] and completion['rows']==11340
    for name,h in completion['files'].items():assert digest(WORK/name)==h,name
    reg=read(ROOT/'registration.json')
    for name,h in reg['files'].items():assert digest(ROOT/name)==h,name
    launch=list((ROOT/'launches').glob('*/python.exit'));assert len(launch)==1 and launch[0].read_text().strip()=='0'
    count_a=count_b=proofs=0
    for domain in ('dev','confirm'):
        inputs=ROOT/'inputs'/domain;index=read(inputs/'fixtures.json')
        pub=Ed25519PublicKey.from_public_bytes((inputs/'TEST_ONLY_ed25519_public.key').read_bytes())
        for x in index['batches']:
            original=codec.old.decode_batch((inputs/x['wires']['full']['path']).read_bytes())
            d=WORK/'reference'/f"{domain}_{x['cell_id']}_b{x['batch_index']}"
            for m in codec.MODES:
                raw=(d/(m+'.wire')).read_bytes();out=codec.decode_batch(raw,m)
                assert out==original and codec.encode_batch(original,m)==raw
                v=codec.host.Verifier(pub,original.previous);v.accept(out);assert v.checkpoint==original.next
                count_a+=1
    for folder in sorted((WORK/'external').glob('*_b*')):
        obj=read(folder/'bundle.json');expected=[]
        for x in obj['Items']:
            p=x['Proof'];expected.append((b64(x['Key']),b64(x['Value']),[b64(v) for v in p['SideNodes'] or []],b64(p['NonMembershipLeafData']),b64(p['SiblingData'])))
        for m in ('ordinary','compact','zlib-ordinary','zlib-compact'):
            root,items=parse_external((folder/(m+'.wire')).read_bytes())
            assert root==b64(obj['Root']) and items==expected
            for it in items:
                assert verify_external(root,it)
                assert not verify_external(bytes(v^255 for v in root),it)
                proofs+=1
            count_b+=1
    rows=[]
    for host,expected_count,modes in [('reference',5292,set(codec.MODES)),('external',6048,{'ordinary','compact','zlib-ordinary','zlib-compact'})]:
        rr=[json.loads(s) for s in (WORK/host/'log.jsonl').read_text().splitlines()]
        assert len(rr)==expected_count
        paired=defaultdict(dict)
        for x in rr:
            assert x['total_ns']==x['encode_ns']+x['decode_ns']+x['verify_ns'] and x['total_ns']>0
            key=(x['domain'],x['cell'],x['batch'],x['repeat']);assert x['mode'] not in paired[key];paired[key][x['mode']]=x
        assert all(set(x)==modes for x in paired.values())
        assert all(len({v['order'] for v in x.values()})==len(modes) for x in paired.values())
        rows+=rr
    recorded=read(WORK/'eval.json');groups=defaultdict(list)
    for x in rows:groups[(x['host'],x['domain'],x['cell'])].append(x)
    summaries=[]
    for c in recorded['cells']:
        rr=groups[(c['host'],c['domain'],c['cell'])];pairs=defaultdict(dict)
        for x in rr:pairs[(x['batch'],x['repeat'])][x['mode']]=x
        base,target=('binary-full','binary-bitmap') if c['host']=='reference' else ('ordinary','compact')
        ratios=[v[target]['total_ns']/v[base]['total_ns'] for v in pairs.values()]
        byteratios=[v[target]['bytes']/v[base]['bytes'] for v in pairs.values()]
        assert statistics.median(ratios)==c['time_ratio'];assert max(byteratios)==c['byte_ratio'];assert len(pairs)==63
        allcomparisons={}
        for mode in next(iter(pairs.values())):
            allcomparisons[mode]={'time_ratio':statistics.median(v[mode]['total_ns']/v[base]['total_ns'] for v in pairs.values()),
                                  'byte_ratio':max(v[mode]['bytes']/v[base]['bytes'] for v in pairs.values())}
        summaries.append(dict(host=c['host'],domain=c['domain'],cell=c['cell'],comparisons=allcomparisons))
    a_diag=read(WORK/'reference/diagnostics.json');b_diag=read(WORK/'external/diagnostics.json')
    for x in a_diag:assert x['sizes']['binary-full']-x['sizes']['binary-bitmap']==32*(255*len(x['retained'])-sum(x['retained']))
    for x in b_diag:assert x['sizes']['ordinary']-x['sizes']['compact']==sum(32*(d-k)-2-m for d,k,m in zip(x['depths'],x['retained'],x['masks']))
    audit={'source_and_artifact_hashes':True,'original_reference_frames':count_a,'external_frames':count_b,'independently_verified_external_proofs':proofs,
           'exact_byte_identities':True,'all_paired_metrics_reproduced':True,'comparisons':summaries}
    (ROOT/'AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k!='comparisons'},indent=2))

if __name__=='__main__':main()
