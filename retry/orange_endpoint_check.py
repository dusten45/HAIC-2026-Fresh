"""Enumerate all upper RGB rounding tuples for public orange/road mixtures.

Conditional on per-channel-downward source alpha/area arithmetic and final
positive INTER_LINEAR followed by <=nearest RGB rounding. No case data.
"""
import json,time,sys
from pathlib import Path
import numpy as np,cv2

def main():
 cpu=time.process_time();bg=109.1;orange=np.array([255.,165.,0.]);breaks=[0.,1.]
 for target in orange:
  for k in range(256):
   f=(k+.5-bg)/(target-bg)
   if 0<=f<=1:breaks.append(f)
 breaks=np.array(sorted(set(breaks)))
 fractions=np.unique(np.clip(np.r_[breaks-1e-10,breaks+1e-10,(breaks[:-1]+breaks[1:])/2],0,1))
 rgb=np.floor(bg+(orange[None,:]-bg)*fractions[:,None]+.5).clip(0,255).astype(np.uint8)
 gray=cv2.cvtColor(rgb[None,:,:],cv2.COLOR_RGB2GRAY)[0]
 assert int(gray.max())==173
 result=dict(background_upper=bg,orange_RGB=orange.tolist(),rounding_breakpoints=len(breaks),evaluated_tuples=len(fractions),max_final_grayscale=int(gray.max()),
  RGB2GRAY_coefficients_15bit=[9798,19235,3735],CPU_s=time.process_time()-cpu,model_ticks=0,native_actions=0,
  proof_scope='All common coverage f in[0,1] and roadRGB channels<=109.1. Earlier alpha/shrink floors preserve a common-coverage componentwise upper RGB line; positive resize then rounds each channel no higher than nearest integer. Every rounding interval and both sides of its endpoints are enumerated. Different backends/materials require review.',
  limitations='Necessary color guard only; peak<=173 does not prove orange identity or reject every antialiased grass shape.')
 out=Path(sys.argv[1]);assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result))
if __name__=='__main__':main()
