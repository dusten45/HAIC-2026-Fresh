"""Plan/source/AST gate only; never imports controller, world or physics."""
import ast,hashlib,json,sys
from pathlib import Path

def run(root):
 d=Path(root)/'stage477-revision1';p=json.loads((d/'plan.json').read_text());h=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();checks={}
 assert h(d/'plan.json')==(d/'plan.sha256').read_text().strip();checks['plan_bound']=True
 for group in ['sources','protected','original408_preserve']:
  for f,v in p[group].items():assert h(f)==v,f
 checks['sources_protected18_ledger']=True
 assert p['caps']==dict(ticks=4096,worlds=49,CPU_s=600,wall_s=900,actual_actions=0,resets=0,max_parallel=1)
 assert p['scope']==dict(ticks=3674,worlds=49);assert p['budget_fixture']['parts']==dict(source=dict(ticks=1242,worlds=35),root_H13=dict(ticks=324,worlds=9),candidate_pending=dict(ticks=108,worlds=3),whole_parents=dict(ticks=2000,worlds=2));checks['counts49_worlds_304allocator']=True
 g=Path(__file__).resolve().parents[1];law=(g/'retry/law477.py').read_text();tree=ast.parse(law);one=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='one477');assert sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='act' for n in ast.walk(one))==1;checks['nominal_once_AST']=True
 whole=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='whole_parents');assert any(isinstance(n,ast.For) and isinstance(n.iter,ast.List) and [x.id for x in n.iter.elts]==['PROJECTED','ALLOCATED'] for n in ast.walk(whole));checks['two_whole_laws_only']=True
 for f in ['compare477.py','meter477.py','law477.py','live477.py','pending477.py','quota477.py','retain477.py']:
  compile((g/'retry'/f).read_text(),f,'exec')
 checks['syntax']=True;assert p['storage_forecast']['semantic_actual_growth_bytes']<=p['storage_forecast']['semantic_growth_hard_allowance_bytes'];checks['source_growth_and_file_quotas_registered']=True
 out=dict(stage=477,passed=True,plan_sha256=h(d/'plan.json'),checks=checks,new_physics=0,new_world=0,new_actual=0,new_reset=0)
 with (d/'static-result.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(json.dumps(out))
if __name__=='__main__':run(sys.argv[1])
