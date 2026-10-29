import castle_fourway as c
import numpy as np

saved=np.load(c.ROOT/'castle_fourway_families.npz')
c.families={key:saved[key] for key in saved.files}
results=np.load(c.ROOT/'castle_fourway_search.npz')
baseweights=results['weights']
top=results['a'][np.argsort(results['s'].mean(axis=1))[-80:]]
c.families['low_castles']=c.soften(top,15000,2,.6)
weights=[]
for i,frac in enumerate([0,.1,.2,.3,.4,.2]):
    weights.append(np.append(baseweights[i]*(1-frac),frac))
weights=np.array(weights)
a=c.grid(2)
table,opponents=c.build_table(weights,256,689245)
s=c.evaluate(a,table,len(weights))
c.summarize(a,s,'adaptive coarse')
a=c.neighbors(c.top_candidates(a,s,240),2)
table,opponents=c.build_table(weights,1024,654783)
s=c.evaluate(a,table,len(weights))
c.summarize(a,s,'adaptive refined')
a=c.top_candidates(a,s,300)
table,opponents=c.build_table(weights,16384,923740)
s=c.evaluate(a,table,len(weights))
c.summarize(a,s,'adaptive validation')
for j in range(len(weights)):
    k=s[:,j].argmax()
    print('scenario best',j,a[k].tolist(),round(float(s[k,j]),4),flush=True)
candidates=np.array([[17,31,51,1,0],[18,30,51,1,0],[0,39,0,61,0],[1,35,0,64,0],[0,36,0,0,64],[0,0,49,51,0],[1,1,1,1,96],[3,5,27,2,63]])
ss=c.evaluate(candidates,table,len(weights))
for aa,row in zip(candidates,ss):print('comparison',aa.tolist(),round(float(row.mean()),4),np.round(row,3).tolist(),flush=True)
np.savez(c.ROOT/'castle_fourway_meta.npz',a=a,s=s,weights=weights)
np.savez(c.ROOT/'castle_fourway_meta_families.npz',**c.families)

# Validate the native scorer against a separate direct implementation.
candidate=a[s.mean(axis=1).argmax()]
direct=[]
pay=np.array([9.,4.,2.,0.])
for opp in opponents[:200]:
    players=np.vstack([candidate,opp])
    mx=players.max(axis=0)
    winner=players==mx
    points=(winner*(12*np.arange(1,6)//winner.sum(axis=0))).sum(axis=1)
    greater=np.count_nonzero(points[1:]>points[0])
    eq=np.count_nonzero(points==points[0])
    direct.append(pay[greater:greater+eq].mean())
small=np.ascontiguousarray(table[:,:,:200,:])
native=c.evaluate(candidate[None,:],small,1)[0,0]
assert abs(native-np.mean(direct))<1e-10
print('independent scorer check passed',candidate.tolist(),native,flush=True)
