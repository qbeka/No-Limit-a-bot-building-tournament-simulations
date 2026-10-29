"""Fresh group draws for fixed allocations; no allocation selection in this run."""
import json
import numpy as np
from pathlib import Path

ROOT=Path(__file__).resolve().parent
seed=430291867
per_scenario=50000
saved=np.load(ROOT/'castle_fourway_meta_families.npz')
families={k:saved[k] for k in saved.files}
weights=np.load(ROOT/'castle_fourway_meta.npz')['weights']
rng=np.random.default_rng(seed)
groups=[]
for row in weights:
    f=rng.choice(len(families),size=(per_scenario,3),p=row)
    a=np.empty((per_scenario,3,5),dtype=np.int16)
    for j,pool in enumerate(families.values()):
        use=f==j
        a[use]=pool[rng.integers(len(pool),size=int(use.sum()))]
    groups.append(a)
opponents=np.concatenate(groups)
allocations={
 'selected_game2':[2,34,3,59,2],
 'near_tie_game2':[2,35,2,59,2],
 'initial_game2':[17,31,51,1,0],
 'selected_game1':[3,5,27,2,63],
 'equal':[20,20,20,20,20],
 'proportional':[7,13,20,27,33],
 'three_high':[0,0,33,33,34],
 'two_high':[0,0,0,49,51],
 'one_high':[1,1,1,1,96],
 'all_five':[0,0,0,0,100],
}
pay12=np.array([[108,78,60,45],[48,36,24,0],[24,12,0,0],[0,0,0,0]])

def mean_interval(x):
    x=x.reshape(len(weights),per_scenario)
    means=x.mean(axis=1)
    se=np.sqrt((x.var(axis=1,ddof=1)/per_scenario).sum())/len(weights)
    mean=float(means.mean())
    return {'mean':mean,'standard_error':float(se),'ci95':[mean-1.96*se,mean+1.96*se],'by_scenario':means.tolist()}

results={}
payouts={}
for name,a in allocations.items():
    own=np.broadcast_to(np.array(a),(len(opponents),1,5))
    players=np.concatenate([own,opponents],axis=1)
    winners=players==players.max(axis=1,keepdims=True)
    castle_points12=winners*(12*np.arange(1,6)//winners.sum(axis=1))[:,None,:]
    scores12=castle_points12.sum(axis=2)
    greater=(scores12[:,1:]>scores12[:,0,None]).sum(axis=1)
    equal=(scores12[:,1:]==scores12[:,0,None]).sum(axis=1)
    payouts[name]=pay12[greater,equal]/12
    result=mean_interval(payouts[name])
    result['allocation']=a
    result['sole_first_rate']=float(((greater==0)&(equal==0)).mean())
    result['tied_first_rate']=float(((greater==0)&(equal>0)).mean())
    result['mean_castle_points']=float(scores12[:,0].mean()/12)
    result['strict_castle_win_rate']=((players[:,0,:]>players[:,1:,:].max(axis=1)).mean(axis=0)).tolist()
    both=(castle_points12[:,0,1]==24)&(castle_points12[:,0,3]==48)
    result['strict_win_castles_2_and_4_rate']=float(both.mean())
    if both.any():
        result['payout_if_strict_win_2_and_4']=float(payouts[name][both].mean())
        result['min_payout_if_strict_win_2_and_4']=float(payouts[name][both].min())
    results[name]=result
    print(name,round(result['mean'],6),[round(x,6) for x in result['ci95']],flush=True)
differences={}
for name in allocations:
    if name!='selected_game2':
        differences[name]=mean_interval(payouts['selected_game2']-payouts[name])
report={
 'description':'Frozen allocations evaluated on fresh independent group draws from previously fixed synthetic family pools.',
 'seed':seed,'groups_per_scenario':per_scenario,'total_groups':len(opponents),
 'family_order':list(families),'scenario_weights':weights.tolist(),
 'limitations':['Intervals quantify group-sampling uncertainty under the finite synthetic model.','They exclude uncertainty about real applicants, family construction, and scenario weights.','No candidate was selected or adjusted using this evaluation.'],
 'results':results,'paired_differences_selected_minus_baseline':differences,
}
(ROOT/'castle_frozen_check.json').write_text(json.dumps(report,indent=2)+'\n')
