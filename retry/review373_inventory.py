"""Supplement readiness inventory with old plans whose workers saved no ready file."""
import json,time,sys,datetime
from pathlib import Path
from retry.path271_run import read,save,sha
G=Path(__file__).resolve().parent.parent

def run(R):
 D=R/'stage373';assert (D/'cost.json').exists() and not (D/'plan-configuration-inventory-private.json').exists();wall,cpu=time.perf_counter(),time.process_time();cfg=read(R/'stage334/configs-private.json');fp={(v['members_sha256']['retry/h1_330_model.py'],v['members_sha256']['retry/temporal_agent.py']):'H'+str(int(h=='ON'))+'F'+str(int(f=='ON')) for h,z in cfg.items() for f,v in z.items()}
 def walk(v,path=''):
  if isinstance(v,dict):
   if 'members_sha256' in v and 'archive_sha256' in v:
    m=v['members_sha256'];cell=fp.get((m.get('retry/h1_330_model.py'),m.get('retry/temporal_agent.py')))
    if cell:return [dict(config_path=path,cell=cell,archive_sha256=v['archive_sha256'])]
   return [r for k,x in v.items() for r in walk(x,path+'/'+k)]
  if isinstance(v,list):return [r for k,x in enumerate(v) for r in walk(x,path+'/'+str(k))]
  return []
 records=[];sources=[Path(__file__),R/'stage334/configs-private.json']
 for stage in range(334,372):
  if stage in [369,371]:continue
  p=R/f'stage{stage}/plan.json'
  if p.exists():records.append(dict(stage=stage,configurations=walk(read(p))));sources.append(p)
 #334fourcells live inconfigs-private, notinlineplan. All other registered
 #plans lackH0F1;335-337 useH1ON, nottheH1OFFcachedcell.
 assert not any(c['cell']=='H0F1' for r in records for c in r['configurations']);assert next(r for r in records if r['stage']==337)['configurations'][0]['cell']=='H1F1'
 private=dict(stage=373,scope='Old334-371plans,excluding369/371;onlyconfigurationhashesextracted. No372or297conditions/results,protectedsplitcontent,actor/envcalls.',records=records,source_hashes={str(p):sha(p) for p in sources});save(D/'plan-configuration-inventory-private.json',private)
 report=read(D/'summary-private.json');report['old_plan_configuration_inventory']=dict(plans_examined=len(records),stages_with_matching_configurations=[r['stage'] for r in records if r['configurations']],registered_H0F1_outside334_configs=0,known335_336_337_actual_base_cell='H1F1',scope='Complementsreadinessfiles;notallpastworkerssavedready.334containsallfourcachedcells,butnative0. NoabsencesofH0F0/H1F0in334+inventoryimplythosehistoricalbaselinesunmeasured;296/330earlieractualrecordsarepreserved.')
 report['additional_metadata_audit_cost']=dict(new_native_actions=0,new_actor_calls=0,wall_s=time.perf_counter()-wall,CPU_s=time.process_time()-cpu,scope='Supplementaloldconfigurationmetadataonly;notanexperimentorbudgetgrant.')
 report['proposed_next_step']=dict(status='Proposalonly;noexecution,reservationornewcandidatebuilt',cell='H0F1R0',artifact_sha256=report['archive_cells']['H0F1'],hypothesis='Existingfixedfallbackrotationmayrepairretainedhazardtransporton296withoutH1pedalselectionorbirthrouting/history. Notanewformulaandnotprovenbenefit;missingactualcellwitholdTRAINcacheevidence.',evidence_only_from='334old296TRAINcache/source/metrics;335-337provenance;olderTRAINandoldDEVresults.372usedsolelyforrejectiondecision.',minimum='OnefrozenexistingH0F1R0T2950episodefromreset,ownpixels/fullcontrols/normalmemory,max2000actions;qualifiedhistorical296reference315/DNFnotrerun.',maximum_new_wrapper_actions=2000,environment_resets=1,maximum_raw_step_ticks=8000,expected_reset_ticks=51,new_grant=0,reserve_use=0,not_currently_reserved=True,paired_option='Ifnewcausalpairedcontrolrequired,registerfreshA296+Bmax4000/2resetsinstead,notinadditionto2000. Historical296hasnoequalfullRNG/actorstateprefixclaim.',preconditions='RequalifyoriginaloldTRAINcase/initialhashes,existingZIP/member/models/runtime/read-onlyobserver/inputlimits;H1disabled,birthrouting/historyabsent,acceptedopticalunchanged. NoGTtocontrol. No newformula/threshold/selector/fit.',stops='Firstofficialfinish/retire,else2000protocolcensor/currentdeadline/technical/integrityorsupportfailure. No retry/substitution/extension. CensorisnotDNF.',falsification='NoT2950officialfinishrejectslocalrescue;noeffect/repeatedfailuredoesnotfalsifyallmotionobservers. Support/legality/technicalgatefailureblocksadvance. Afinishonlypasseslocalfeasibility,nopromotion.',conditional_next_gate='Onlyafterlocalfinishandgates,aseparateT2954regressioncontractmax2000againstqualifiedold29627.440s;retainofficialfinish,strictlynoautofullTRAINorDEV. BothT2950rescueandT2954preservationneededbeforeanybroadercontract. No newDEV/HOLDOUT/SEALEDopened.',interpretation='Oldcachedoutputsareconditionedon296pixelsandstoredcommands;ONreturnedsteeringfloat32vsnormalfloat64nominalmemoryandfuturepixelsnotactuallyexecuted. Firstdifference28isnotguaranteedlivebranch;149notforced. Neithernewscore nornewindependentsafetyproof.')
 save(D/'summary-private.json',report);save(G/'retry/review373_result.json',report);print(json.dumps(dict(plan_inventory=report['old_plan_configuration_inventory'],missing_cell=report['missing_cell'],proposed_max=2000,newcalls=0)),flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
