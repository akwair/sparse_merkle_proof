import json
from pathlib import Path
import pytest
import run_screening as r

def test_registration_rejects_changed_file(tmp_path):
    p=tmp_path/'PLAN.md';p.write_text('frozen')
    reg={'files':{'PLAN.md':r.sha(p)}}
    assert r.validate(tmp_path,reg) is None
    p.write_text('changed')
    with pytest.raises(ValueError):r.validate(tmp_path,reg)

def test_registration_path_escape(tmp_path):
    with pytest.raises(ValueError):r.validate(tmp_path,{'files':{'../x':'0'*64}})

def test_refuse_existing_run(tmp_path):
    with pytest.raises(FileExistsError):r.create_workdir(tmp_path)

def test_paired_ratios_and_gate():
    rows=[]
    for rep,(a,b) in enumerate(((1,2),(100,50),(10,6))):
        for m,t in [('binary-full',a),('binary-bitmap',b)]:
            rows.append({'host':'reference','domain':'dev','cell':'x','batch':0,'repeat':rep,'mode':m,'bytes':100 if m=='binary-full' else 50,'total_ns':t,'encode_ns':t,'decode_ns':0,'verify_ns':0})
    report=r.evaluate(rows)
    cell=report['cells'][0]
    assert cell['time_ratio']==0.6 # median of paired ratios, not ratio of medians
    assert cell['pass'] is True
    rows[0]['bytes']=0
    with pytest.raises(ValueError):r.evaluate(rows)

def test_missing_pair_fails():
    with pytest.raises(ValueError): r.evaluate([{'host':'reference','domain':'dev','cell':'x','batch':0,'repeat':0,'mode':'binary-full','bytes':10,'total_ns':10}])
