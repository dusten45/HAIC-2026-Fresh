"""216-tick source gate before any native reset; original H13 inputs only."""
import copy
from dataclasses import asdict
from pathlib import Path
from retry.continuation447 import Study447
from retry.pilot420_backend import capture_context,snapshot,fingerprint,rnghash,TechnicalStop
from retry.live447 import check_historical_h13
from retry.audit439 import replay
from retry.ledger439 import compare_first,require
from retry.pilot421_run import compare_frames
from retry.loss389_analyze import read,save

class Qualify448(Study447):
    def qualify448(self):
        records={}
        for recipe in ['nominal','fullgas']:
            archive=read(Path(self.p['archives'][recipe]));pair=[]
            held=self.new(self.state,self.memory,self.actual,'source_'+recipe+'_held')
            before=copy.deepcopy(held.ctrl.memory());nominal=held.ctrl.act(held.m)
            ph,mh,rh=fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash()
            for rep in [1,2]:
                c=self.new(self.state,self.memory,self.actual,'source_'+recipe+str(rep),recipe)
                try:
                    c.initial13('448_source_H13');check_historical_h13(c,archive)
                    audit=None
                    if recipe=='nominal':
                        audit=replay(c.rows,self.rows[22:35],self.fixed)
                        require(audit['certified_prefix_actions']==13 and audit['fresh_current_first_pass']>=1,'448_SOURCE_G1_FACTUAL')
                        compare_first(self.actual,c.rows[0],self.rows[22],self.fixed)
                    require((fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash())==(ph,mh,rh),'448_SOURCE_HELD_MUTATION')
                    self.assert_actual();pair.append(dict(signature=c.signature(),first=copy.deepcopy(c.rows[0]),audit=audit))
                finally:self.close(c)
            require(pair[0]==pair[1],'448_SOURCE_REPEAT')
            held.one('448_source_held_first',first_override=pair[0]['first']['command'],prepared_nominal=nominal,prepared_before=before)
            proof=compare_frames(held.rows[0],pair[0]['first'])
            require(proof['passed'] and not proof['wheel']['clipped_flag_mismatches'],'448_SOURCE_HELD_FIRST')
            require(all(held.rows[0][k]==pair[0]['first'][k] for k in ['command','memory_before','memory_after']),'448_SOURCE_HELD_MEMORY')
            self.close(held);self.assert_actual()
            records[recipe]=dict(historical_H13_exact=True,repeat_exact=True,held_first_passed=True,actual_factual_gate=pair[0]['audit'],candidate_actual_qualified=False)
        require((self.meter.b['ticks'],self.meter.b['worlds'])==(216,6),'448_SOURCE_COST')
        self.meter.qualification_passed=True
        save(self.d/'source-qualification-private.json',dict(passed=True,records=records,ticks=216,worlds=6,new_native_resets=0));return records
