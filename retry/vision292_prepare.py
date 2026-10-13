"""Complete identical291 LORO, reuseN2 models/split without extra fit."""
import argparse
from pathlib import Path
from retry.path271_run import read,save,sha

def run(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage292';assert not D.exists();D.mkdir(mode=0o700);S=R/'stage291';p=read(S/'plan.json');assert p['heldout_road']=='N2' and sha(G/'retry/vision291_fit.py')==p['hashes'][str(G/'retry/vision291_fit.py')];old=read(S/'fit-summary.json');assert old['fit_episodes']==10 and old['test_episodes']==2
 sources=[G/'retry/vision291_fit.py',G/'retry/vision292_fold.py',G/'retry/vision292_prepare.py',S/'plan.json',S/'fit-summary.json',S/'prediction-private.json',S/'feature28-private.pt',S/'pixel_plus28-private.pt',S/'collection-outcome-private.json',R/'project-effective-budget-v297.json']+[q for q in S.glob('*_*/observations-private.npz')]
 plan=dict(stage=292,source_stage=291,new_folds=['O0','O2','N0','N1','N3'],reuse_fold='N2',new_predictor_fits=10,reused_predictor_fits=2,recipe=p['training'],predictors=p['predictors'],preprocessing=p['pixels'],features=p['features'],sample_rule=p['sample_rule'],test='Bothwholeepisodes perheldroad; sameepisodes forbothmodels; trainother5roads; fit-onlymean/std',aggregation='6roadsequal,2episodes/roadequal; complete6/DNF6 errors; no treating1145frame rows asindependentepisodes',native=0,source_physics=0,no_architecture_epoch_grid=True,no_new_data_policy=True,no_HOLDOUT_SEALED=True,no_reserve=True,hashes={str(q):sha(q) for q in sources});save(D/'plan.json',plan);save(D/'N2-reuse-receipt.json',dict(source_summary_sha256=sha(S/'fit-summary.json'),source_predictions_sha256=sha(S/'prediction-private.json'),source_model_sha256={n:sha(S/(n+'-private.pt')) for n in ['feature28','pixel_plus28']},same_recipe_split_preprocessing_verified=True,new_fits=0));print('292new5folds fixed; N2cachedmodels verified, native0',flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
