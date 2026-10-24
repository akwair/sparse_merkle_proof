import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('analysis',Path(__file__).with_name('analyze.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

class AnalysisTests(unittest.TestCase):
 def test_payload_model_units_and_quadrants(self):
  rows=[]
  vals=[(100,1000),(90,2000),(110,500),(90,500),(110,2000),(100,1000),(100,500),(100,2000),(90,1000)]
  for rep in range(21):
   for m,(size,t) in zip(a.MODES,vals):rows.append(dict(domain='dev',cell='x',batch=0,repeat=rep,mode=m,bytes=size,total_ns=t))
  out={r['mode']:r for r in a.payload_model(rows)}
  self.assertEqual(out['compact']['favorable_region'],'below')
  self.assertEqual(out['compact']['boundary_payload_bits_s'],80000000)
  self.assertEqual(out['dictionary']['favorable_region'],'above')
  self.assertEqual(out['dictionary']['boundary_payload_bits_s'],160000000)
  self.assertEqual(out['zlib-ordinary']['favorable_region'],'all')
  self.assertEqual(out['zlib-compact']['favorable_region'],'none')
  self.assertEqual(out['zlib-dictionary']['favorable_region'],'tie')
 def test_registered_matrix_rejects_wrong_pair_labels(self):
  rows,diags=self.matrix();rows[0]['repeat']=99
  with self.assertRaises(ValueError):a.validate_matrix(rows,diags)
 def test_registered_matrix_rejects_duplicate_diagnostics(self):
  rows,diags=self.matrix();diags[-1]=dict(diags[0])
  with self.assertRaises(ValueError):a.validate_matrix(rows,diags)
 def test_registered_matrix_rejects_changed_wire_size(self):
  rows,diags=self.matrix();rows[0]['bytes']=101
  with self.assertRaises(ValueError):a.validate_matrix(rows,diags)
 def test_registered_matrix_accepts_complete_labels(self):
  rows,diags=self.matrix();a.validate_matrix(rows,diags)
 def matrix(self):
  rows=[];diags=[]
  for dom in ('dev','confirm'):
   for n in (4096,16384):
    for q in (1,8,32,128):
     for k in ('member','absent'):
      for p in ('dispersed','clustered'):
       for b in range(3):
        cell=f'n{n}_q{q}_{k}_{p}';d=dict(domain=dom,n=n,q=q,kind=k,pattern=p,batch=b,cell=cell,id=f'{dom}_{cell}_b{b}',sizes={m:100 for m in a.MODES},depths=[1]*q,retained=[1]*q,masks=[1]*q,occurrences=q,zero_occurrences=0,nonzero_occurrences=q,unique_nonzero_nodes=1,unique_nodes=1);diags.append(d)
        for rep in range(21):
         for order,m in enumerate(a.MODES):rows.append({**{x:d[x] for x in ('domain','n','q','kind','pattern','batch','cell','id')},'repeat':rep,'order':order,'mode':m,'bytes':100})
  return rows,diags
 def test_paired_ratio_not_ratio_of_medians(self):
  rows=[]
  for rep,(base,target) in enumerate([(1,2),(100,50),(2,2)]):
   for mode,t in [('ordinary',base),('dictionary',target)]:
    rows.append(dict(domain='dev',cell='x',batch=0,repeat=rep,mode=mode,bytes=100 if mode=='ordinary' else 50,total_ns=t,encode_ns=0,decode_ns=0,verify_ns=t,n=1,q=1,kind='member',pattern='dispersed'))
  c=a.summarize_cells(rows,required_modes={'ordinary','dictionary'},expected_pairs=3)[0]
  self.assertEqual(c['modes']['dictionary']['paired_total_ratio'],1)
 def test_missing_pair_rejected(self):
  with self.assertRaises(ValueError):
   a.summarize_cells([dict(domain='dev',cell='x',batch=0,repeat=0,mode='ordinary',bytes=1,total_ns=1,encode_ns=0,decode_ns=0,verify_ns=1)],required_modes={'ordinary','dictionary'},expected_pairs=1)
 def test_zero_clock_rejected(self):
  with self.assertRaises(ValueError):a.summarize_cells([dict(domain='dev',cell='x',batch=0,repeat=0,mode='ordinary',bytes=1,total_ns=0,encode_ns=0,decode_ns=0,verify_ns=0)],required_modes={'ordinary'},expected_pairs=1)
 def test_stage_mismatch_rejected(self):
  with self.assertRaises(ValueError):a.summarize_cells([dict(domain='dev',cell='x',batch=0,repeat=0,mode='ordinary',bytes=1,total_ns=2,encode_ns=0,decode_ns=0,verify_ns=1)],required_modes={'ordinary'},expected_pairs=1)

if __name__=='__main__':unittest.main()
