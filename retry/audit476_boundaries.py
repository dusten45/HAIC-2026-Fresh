"""Independent certificate metadata/rank identities; no search or physics."""
import struct

def verify_rank_metadata(p):
 rank=struct.unpack('>Q',struct.pack('>d',p['objective']))[0]
 assert rank==p['threshold_rank']
 previous=None if rank==0 else struct.unpack('>d',struct.pack('>Q',rank-1))[0]
 assert p['threshold_predecessor']==previous
 q=struct.unpack('>f',struct.pack('>I',p['q_rank']))[0]
 q0=struct.unpack('>f',struct.pack('>I',p['q0_rank']))[0]
 assert q==p['q'] and q0==p['q0'] and p['domain_rank_lo']<=p['q_rank']<=p['q0_rank']
 assert p['threshold_predecessor_empty'] is True
 return True
