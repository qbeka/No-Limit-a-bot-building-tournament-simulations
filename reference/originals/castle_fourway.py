import ctypes
import itertools
import json
import numpy as np
from pathlib import Path

ROOT=Path('/workspace/scratch/777e389e754a')
rng=np.random.default_rng(872465293)
lib=ctypes.CDLL(str(ROOT/'castle_eval.so'))
lib.evaluate.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_void_p]

def round_rows(x):
    a=np.floor(x).astype(np.int16)
    k=100-a.sum(axis=1)
    idx=np.argsort(x-a,axis=1)[:,::-1]
    for j in range(5):
        rows=np.flatnonzero(k>j)
        a[rows,idx[rows,j]]+=1
    assert np.all(a.sum(axis=1)==100)
    return a

def soften(centers,n,scale=3,atom=.35):
    base=np.asarray(centers)[rng.integers(len(centers),size=n)]
    x=np.maximum(0,base+rng.normal(0,scale,base.shape))
    a=round_rows(x/x.sum(axis=1,keepdims=True)*100)
    exact=rng.random(n)<atom
    a[exact]=base[exact]
    return a

N=15000
families={}
families['balanced']=soften([[20,20,20,20,20],[7,13,20,27,33],[6,13,20,27,34],[5,10,20,30,35],[5,10,15,25,45],[10,15,20,25,30]],N,4,.45)
families['high3']=soften([[0,0,33,33,34],[0,0,25,33,42],[0,0,25,35,40],[0,0,30,35,35],[0,0,20,35,45],[1,1,32,33,33],[1,1,26,35,37],[2,2,26,34,36],[0,0,31,31,38]],N,4,.5)
families['high2']=soften([[0,0,0,50,50],[0,0,0,49,51],[0,0,0,45,55],[0,0,0,44,56],[1,1,1,46,51],[1,1,1,41,56],[2,2,2,41,53],[1,1,36,1,61],[1,1,41,1,56],[0,0,50,0,50],[0,0,0,40,60],[0,0,40,0,60],[0,0,0,35,65]],N,4,.4)
families['one_big']=soften([[0,0,0,0,100],[1,1,1,1,96],[0,0,0,20,80],[0,0,25,0,75],[0,20,0,0,80],[0,25,0,0,75],[1,21,1,1,76],[5,15,0,0,80],[0,0,0,100,0],[0,0,0,80,20],[0,0,0,70,30],[0,0,0,30,70]],N,4,.35)
families['split_small']=soften([[10,20,0,0,70],[11,21,0,0,68],[10,21,1,1,67],[13,21,0,0,66],[0,26,0,0,74],[1,1,27,1,70],[3,5,27,2,63],[5,10,0,26,59],[10,20,30,40,0],[15,25,25,35,0],[0,21,31,48,0],[11,21,0,68,0],[11,0,31,58,0]],N,3,.35)
fam=[]
v=np.arange(1,6)
for i in range(N):
    k=rng.choice([1,2,3,4,5],p=[.05,.35,.3,.2,.1])
    active=rng.choice(5,size=k,replace=False,p=v/v.sum())
    x=np.zeros(5);x[active]=rng.dirichlet(v[active]*rng.choice([.3,1,5]))*100
    fam.append(x)
families['diverse']=round_rows(np.array(fam))

def build_table(weights,per,seed):
    local=np.random.default_rng(seed)
    draws=[]
    for row in weights:
        f=local.choice(len(families),size=(per,3),p=row)
        arr=np.empty((per,3,5),dtype=np.int16)
        for i,pool in enumerate(families.values()):
            wh=f==i
            arr[wh]=pool[local.integers(len(pool),size=int(wh.sum()))]
        draws.append(arr)
    opponents=np.concatenate(draws)
    groups=len(opponents)
    table=np.zeros((5,101,groups,4),dtype=np.int8)
    for j in range(5):
        opp=opponents[:,:,j]
        mx=opp.max(axis=1)
        winners=opp==mx[:,None]
        n=winners.sum(axis=1)
        for x in range(101):
            win=x>mx;tie=x==mx
            table[j,x,win,0]=12*(j+1)
            table[j,x,tie,0]=12*(j+1)//(n[tie]+1)
            pts=12*(j+1)//(n+tie)
            pts[win]=0
            table[j,x,:,1:]=winners*pts[:,None]
    return np.ascontiguousarray(table),opponents

def evaluate(a,table,scenarios):
    a=np.ascontiguousarray(a,dtype=np.int16)
    out=np.empty((len(a),scenarios),dtype=np.float64)
    lib.evaluate(a.ctypes.data,len(a),table.ctypes.data,table.shape[2],scenarios,out.ctypes.data)
    return out

def grid(step):
    total=100//step;out=[]
    for a in range(total+1):
        for b in range(total+1-a):
            for c in range(total+1-a-b):
                d=np.arange(total+1-a-b-c,dtype=np.int16)
                out.append(np.column_stack([np.full(len(d),a),np.full(len(d),b),np.full(len(d),c),d,total-a-b-c-d]))
    return np.vstack(out).astype(np.int16)*step

def top_candidates(a,s,k=200):
    ix=set(np.argsort(s.mean(axis=1))[-k:].tolist())
    for j in range(s.shape[1]):ix.update(np.argsort(s[:,j])[-k//3:].tolist())
    ix.update(np.argsort(s.min(axis=1))[-k//3:].tolist())
    return a[sorted(ix)]

def neighbors(a,radius):
    deltas=np.array([(*d,-sum(d)) for d in itertools.product(range(-radius,radius+1),repeat=4) if abs(sum(d))<=radius],dtype=np.int16)
    all_a=(a[:,None,:]+deltas[None,:,:]).reshape(-1,5)
    all_a=all_a[(all_a>=0).all(axis=1)&(all_a<=100).all(axis=1)]
    return np.unique(all_a,axis=0)

def summarize(a,s,label):
    print(label,flush=True)
    for k in np.argsort(s.mean(axis=1))[-8:][::-1]:
        print(a[k].tolist(),round(float(s[k].mean()),4),np.round(s[k],3).tolist(),flush=True)

if __name__=='__main__':
    weights=np.array([
      [.25,.30,.20,.10,.05,.10],
      [.05,.25,.35,.15,.10,.10],
      [.05,.10,.20,.35,.20,.10],
      [.05,.10,.15,.15,.35,.20],
      [.10,.10,.15,.10,.15,.40],
      [.05,.05,.15,.40,.25,.10],
    ])
    table,opponents=build_table(weights,128,782364)
    a=grid(2)
    print('coarse actions',len(a),'sample groups',len(opponents),flush=True)
    s=evaluate(a,table,len(weights));summarize(a,s,'coarse')
    a=neighbors(top_candidates(a,s,240),2)
    print('refined actions',len(a),flush=True)
    table,opponents=build_table(weights,512,829047)
    s=evaluate(a,table,len(weights));summarize(a,s,'refined')
    a=top_candidates(a,s,250)
    table,opponents=build_table(weights,8192,9830124)
    s=evaluate(a,table,len(weights));summarize(a,s,'validation')
    np.savez(ROOT/'castle_fourway_search.npz',a=a,s=s,weights=weights)
    np.savez(ROOT/'castle_fourway_families.npz',**families)
    candidates=np.array([[3,5,27,2,63],[0,0,0,0,100],[1,1,1,1,96],[10,20,0,0,70],[11,21,0,0,68],[0,26,0,0,74],[1,1,36,1,61],[1,1,1,41,56],[0,0,0,49,51],[0,0,33,33,34]])
    s=evaluate(candidates,table,len(weights))
    for a,row in zip(candidates,s):print('baseline',a.tolist(),round(float(row.mean()),3),np.round(row,3).tolist(),flush=True)
