import itertools
import numpy as np

rng = np.random.default_rng(5462938)
v = np.arange(1, 6)
N = 30000

def round_rows(x):
    a = np.floor(x).astype(int)
    k = 100 - a.sum(axis=1)
    idx = np.argsort(x-a, axis=1)[:, ::-1]
    for j in range(5):
        rows = np.flatnonzero(k > j)
        a[rows, idx[rows, j]] += 1
    assert np.all(a.sum(axis=1) == 100)
    return a

def marginals(a):
    p = np.array([np.bincount(a[:,j], minlength=101) for j in range(5)]) / len(a)
    return (np.cumsum(p, axis=1)-.5*p)*v[:,None]

def best(g):
    dp = np.full(101, -1e10); dp[0] = 0
    idx = np.arange(101)
    rem = idx[:,None]-idx[None,:]
    valid = rem >= 0
    trace=[]
    for j in range(5):
        q=dp[np.maximum(rem,0)] + g[j][None,:]
        q[~valid]=-1e10
        take=q.argmax(axis=1)
        dp=q[idx,take]
        trace.append(take)
    a=[]; b=100
    for take in trace[::-1]:
        k=int(take[b]); a.append(k); b-=k
    return np.array(a[::-1]), float(dp[-1])

def soften(centers, n, scale=2.5, atom=.4):
    base = centers[rng.integers(len(centers),size=n)]
    x = np.maximum(0, base + rng.normal(0,scale,base.shape))
    x = x / x.sum(axis=1,keepdims=True)*100
    a = round_rows(x)
    exact=rng.random(n)<atom
    a[exact]=base[exact]
    return a

families={}
families['equal']=soften(np.array([[20]*5]),N,4,.4)
families['weighted']=soften(np.array([[7,13,20,27,33],[6,13,20,27,34],[10,15,20,25,30],[5,10,20,30,35],[5,10,15,30,40],[5,10,15,25,45],[5,15,20,25,35]]),N,4,.4)
three=np.array([[0,0,33,33,34],[0,0,34,33,33],[0,0,25,33,42],[0,0,25,35,40],[0,0,30,35,35],[0,0,20,35,45],[0,0,31,31,38],[1,1,32,33,33],[1,1,31,33,34],[1,1,26,35,37],[2,2,26,34,36]])
families['high3']=soften(three,N,4,.5)
two=np.array([[0,0,0,50,50],[0,0,0,49,51],[0,0,0,45,55],[0,0,0,44,56],[1,1,1,46,51],[1,1,1,41,56],[2,2,2,41,53],[1,1,36,1,61],[1,1,41,1,56],[0,0,50,0,50],[0,0,0,40,60]])
families['high2']=soften(two,N,4,.4)
fam=[]
for i in range(N):
    k = rng.choice([2,3,4,5],p=[.15,.35,.3,.2])
    active = rng.choice(5,size=k,replace=False,p=v/v.sum())
    x=np.zeros(5)
    x[active]=rng.dirichlet(v[active]*rng.choice([.3,1,5]))*100
    fam.append(x)
families['diverse']=round_rows(np.array(fam))
g=np.array([marginals(a) for a in families.values()])
names=list(families)
# Construct higher reasoning levels by optimizing against many assumed mixtures.
meta=[]
for _ in range(500):
    w=rng.dirichlet([1,2,4,3,2])
    b,_=best(np.einsum('f,fij->ij',w,g))
    meta.append(b)
families['meta1']=soften(np.array(meta),N,2,.4)
g=np.array([marginals(a) for a in families.values()])
meta=[]
for _ in range(500):
    w=rng.dirichlet([.5,1,2,2,2,4])
    b,_=best(np.einsum('f,fij->ij',w,g))
    meta.append(b)
families['meta2']=soften(np.array(meta),N,2,.4)
g=np.array([marginals(a) for a in families.values()])
names=list(families)
scenarios=np.array([
    [.15,.30,.25,.10,.15,.04,.01],
    [.05,.15,.35,.20,.10,.10,.05],
    [.03,.07,.20,.30,.10,.20,.10],
    [.02,.08,.15,.15,.15,.30,.15],
    [.03,.07,.10,.15,.20,.20,.25],
    [.02,.08,.20,.10,.40,.10,.10],
])
scg=np.einsum('sf,fij->sij',scenarios,g)
bestsc=np.array([best(q)[1] for q in scg])
print('families',names,flush=True)
for i,q in enumerate(g):
    print('Family best',names[i],best(q),flush=True)
for i,q in enumerate(scg):
    print('Scenario best',i,best(q),flush=True)
# Enumerate all 4,598,126 integer allocations exactly for model robustness.
all_a=[]
for a in range(101):
    for b in range(101-a):
        for c in range(101-a-b):
            d=np.arange(101-a-b-c,dtype=np.int16)
            all_a.append(np.column_stack([np.full(len(d),a),np.full(len(d),b),np.full(len(d),c),d,100-a-b-c-d]))
A=np.vstack(all_a).astype(np.int16)
print('allocations',len(A),flush=True)
S=sum(scg[:,i,A[:,i]] for i in range(5)).T
avg=S.mean(axis=1)
reg=(bestsc-S).max(axis=1)
for label,objective in [('average',avg),('minimax_regret',-reg),('lowest_scenario',S.min(axis=1)),('average_regret',avg-.5*reg)]:
    k=objective.argmax()
    a=A[k]
    print(label,a.tolist(),'scenarios',np.round(S[k],4).tolist(),'family',np.round(sum(g[:,i,a[i]] for i in range(5)),4).tolist(),flush=True)
for a in [[1,1,1,41,56],[2,2,2,41,53],[3,3,3,39,52],[1,1,36,1,61],[1,1,41,1,56],[2,2,36,2,58],[2,2,2,38,56],[1,1,26,35,37],[2,2,27,36,33],[7,13,20,27,33]]:
    print('candidate',a,'scenarios',np.round(sum(scg[:,i,a[i]] for i in range(5)),3).tolist(),'family',np.round(sum(g[:,i,a[i]] for i in range(5)),3).tolist(),flush=True)
np.savez('/workspace/scratch/777e389e754a/castle_analysis.npz',g=g,scg=scg,A=A,S=S)
