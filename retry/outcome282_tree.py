"""Fixed depth2,minleaf3 CART Gini; deterministic split/class tie rules, no search."""
import numpy as np
CLASSES=['baseline','gas_upper','brake_lower','steer_plus','steer_minus']
def fit(X,y,depth=0):
 X=np.asarray(X,float);y=np.asarray(y,int);counts=np.bincount(y,minlength=5);prediction=int(np.argmax(counts));node=dict(samples=len(y),counts=counts.tolist(),prediction=prediction)
 if depth==2 or len(y)<6 or np.count_nonzero(counts)==1:return node
 def impurity(labels):
  c=np.bincount(labels,minlength=5);return len(labels)*(1-np.sum((c/len(labels))**2))
 best=None;parent=impurity(y)
 for f in range(16):
  values=np.unique(X[:,f])
  for l,r in zip(values[:-1],values[1:]):
   threshold=float(l+(r-l)/2);left=X[:,f]<=threshold;n=int(left.sum())
   if n<3 or len(y)-n<3:continue
   score=impurity(y[left])+impurity(y[~left])
   if score<parent and (best is None or score<best[0]):best=(score,f,threshold,left)
 if best is None:return node
 _,f,t,left=best;node.update(feature=f,threshold=t,left=fit(X[left],y[left],depth+1),right=fit(X[~left],y[~left],depth+1));return node
def predict(tree,X):
 out=[]
 for x in X:
  node=tree
  while 'feature' in node:node=node['left'] if x[node['feature']]<=node['threshold'] else node['right']
  out.append(node['prediction'])
 return np.array(out,int)
