"""Pure boundary/storage fixtures supplement the fixed scalar counterexample run."""
import hashlib,json,math,tempfile,unittest
from unittest import mock
from fractions import Fraction as F
from pathlib import Path
from retry import envelope500 as e
from retry.storage500 import Store500,StorageStop,LIMITS,FINAL_MAX,TOTAL,FILES_MAX

class Boundaries(unittest.TestCase):
    def test_zero_closed_and_smallest_float(self):
        z,c=e.solve(1.,10.,10.,[0.,1.1,100.],[0.,10.,100.])
        self.assertEqual(z['accel'],0.)
        self.assertFalse(e.residuals(c,0.))
        self.assertTrue(e.residuals(c,math.nextafter(0.,math.inf)))
        self.assertFalse(e.residuals(c,math.nextafter(0.,-math.inf)))
    def test_crossing_seam_both_owners(self):
        c=e.context(1.,25.,25.,[0.,2.,100.],[0.,25.,100.])
        for a in [math.nextafter(0.,-math.inf),0.,math.nextafter(0.,math.inf)]:
            # Exact d=1 and sigma=25 put the node exactly on t=2/50.
            self.assertEqual(bool(e.residuals(c,a)),a>0)
    def test_current_node_and_empty(self):
        e.solve(1.,10.,10.,[0.,1.,100.],[0.,10.,100.])
        with self.assertRaisesRegex(e.EnvelopeStop,'EMPTY_SET'):
            e.solve(1.,11.,11.,[0.,1.,100.],[0.,10.,100.])
    def test_crossed_extraneous_root(self):
        # r-v+sigma<0: squared elimination alone would accept an invalid root.
        c=e.context(1.,20.,1.,[0.,1.001,100.],[0.,1.,100.])
        self.assertTrue(e.residuals(c,0.))
    def test_stationary_and_progress_zero(self):
        z,c=e.solve(1.,0.,0.,[0.,100.],[0.,50.]);self.assertGreater(z['accel'],0)
        self.assertEqual(c['low'],0)
        with self.assertRaisesRegex(e.EnvelopeStop,'EMPTY_SET'):
            e.solve(1.,30.,0.,[0.,1.01,100.],[0.,1.,100.])
    def test_no_wrap_and_handoff(self):
        z,c=e.solve(99.9,10.,10.,[0.,100.],[0.,12.])
        a=z['accel'];self.assertGreater(99.9+10*.08+.5*a*.08**2,100.)
        # Beyond-L surrogate is allowed only within this hold; no launch node
        # reappears. Next own current state at/beyond L requires actual terminal
        # handoff or STOP, never fabricated finish.
        self.assertEqual(len(c['nodes']),1)
        for s in (100.,100.1):
            with self.assertRaises(e.EnvelopeStop):e.solve(s,10.,10.,[0.,100.],[0.,12.])
        with self.assertRaisesRegex(e.EnvelopeStop,'EXISTING_PHASE_HANDOFF'):
            e.act([0.,0.,0.],'FINISH_CONFIRM',99.9,10.,10.,[0.,100.],[0.,12.])
    def test_float32_rounding_is_not_zero_error(self):
        z,c=e.solve(1.,20.,20.,[0.,1000.],[0.,100.]);m=e.command(z,c,.2)
        self.assertNotEqual(m['scalar_mapping_error'],0.)
        self.assertFalse(e.residuals(c,m['scalar_mapped_accel']))
        self.assertEqual(m['action'][0],e.float32(.2))
        self.assertFalse(m['physical_tyre_feasible_claimed'])
    def test_unrepresentable_pedal_interval_stops(self):
        # Exact singleton acceleration -1, source-map ideal brake is not f32.
        c={'low':F(-1),'high':F(-1),'v':F(10),'sigma':F(10),'nodes':()}
        with self.assertRaisesRegex(e.EnvelopeStop,'FLOAT32_MAPPING_EMPTY_OR_UNCERTIFIED'):
            e.command({'accel':-1.},c,0.)
    def test_closed_singleton_and_no_binary64(self):
        z,c=e.solve(1.,6.375,6.25,[0.,1.25,100.],[0.,.125,100.])
        self.assertEqual(z['accel'],-78.125)
        self.assertEqual(F(z['accel']),c['low'])
        with self.assertRaisesRegex(e.EnvelopeStop,'FLOAT32_MAPPING_EMPTY_OR_UNCERTIFIED'):
            e.command(z,c,0.)
        # Construct an exact dyadic stopping node; exact lower endpoint has
        # more significand bits than binary64 and is the only real feasible a.
        d=(2**47+1)/2**50; sigma=d*25;v=sigma+.125
        c=e.context(1.,v,sigma,[0.,1.+d,100.],[0.,.125,100.])
        self.assertFalse(e.residuals(c,c['low']))
        self.assertNotEqual(F(float(c['low'])),c['low'])
        with self.assertRaisesRegex(e.EnvelopeStop,'EMPTY_BINARY64'):
            e.solve(1.,v,sigma,[0.,1.+d,100.],[0.,.125,100.])
    def test_invalid_finite_and_nonfinite(self):
        for x in [math.nan,math.inf,-math.inf]:
            with self.assertRaises(e.EnvelopeStop):e.solve(1.,x,0.,[0.,100.],[0.,10.])
        for sigma in [-1.,-5e-324]:
            with self.assertRaisesRegex(e.EnvelopeStop,'REVERSE'):e.solve(1.,10.,sigma,[0.,100.],[0.,10.])
    def test_signed_zero_pedal_owner(self):
        self.assertEqual(e.next32(-0.,True),e.next32(0.,True))
        self.assertGreater(e.next32(-0.,True),0.)
        self.assertIsNone(e.next32(-0.,False))
    def test_exact_time_and_mass(self):
        self.assertEqual(e.TIMES,tuple(F(k,50) for k in range(1,5)))
        self.assertNotEqual(e.TAU,F(.08))
        self.assertEqual(e.MASS,29.249793766661764)
        self.assertNotEqual(e.MASS,29.24979)

class Storage(unittest.TestCase):
    def test_worst_case_ledger_without_bulk_allocation(self):
        q=Store500();q.closing=True
        for kind,(count,size,_) in LIMITS.items():
            # Metadata16MiB uses127 entries; one file slot is reserved for atomic temp.
            count=127 if kind=='other' else count
            for i in range(count):
                n=(256*1024 if i==0 else 128*1024) if kind=='other' else size
                q.record(kind+str(i),kind,n,'synthetic-no-bytes')
        self.assertEqual(sum(q.sizes.values()),FINAL_MAX)
        self.assertEqual(len(q.used)+1,FILES_MAX)
        self.assertLessEqual(sum(q.sizes.values())+max(v[1] for v in LIMITS.values()),TOTAL)
        with self.assertRaises(StorageStop):q.record('extra','other',1,'x')
    def test_limits_before_write_and_final_bytes(self):
        q=Store500()
        with self.assertRaisesRegex(StorageStop,'CATEGORY'):q.publish('oversize','tick',b'x'*(16*1024+1))
        self.assertFalse(q.used)
        with self.assertRaisesRegex(StorageStop,'FINAL_BYTES'):q.publish('dict','tick',{})
        with self.assertRaisesRegex(StorageStop,'ENTRY_NAME'):q.publish('../bad','other',b'{}')
    def test_interned_readback_and_immutability(self):
        with tempfile.TemporaryDirectory() as tmp:
            q=Store500(Path(tmp)/'synthetic');a=q.intern_state(b'{"synthetic":true}')
            self.assertEqual(q.intern_state(b'{"synthetic":true}'),a)
            self.assertEqual(q.counts['state'],1)
            with self.assertRaisesRegex(StorageStop,'IMMUTABLE'):q.publish(a['name'],'state',b'changed')
            self.assertEqual((q.root/a['name']).read_bytes(),b'{"synthetic":true}')
    def test_write_failure_blocks_all_later_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            q=Store500(Path(tmp)/'synthetic')
            with mock.patch('retry.storage500.os.link',side_effect=OSError('synthetic failure')):
                with self.assertRaises(OSError):q.publish('failed.json','other',b'{}')
            self.assertTrue(q.failed)
            self.assertTrue((q.root/'failed.json.tmp500').exists())
            with self.assertRaisesRegex(StorageStop,'FAILED_WRITE_NO_MORE_OUTPUT'):
                q.publish('no-closeout.json','other',b'{}')
    def test_closing_reserve(self):
        q=Store500()
        for i in range(120):q.record('m'+str(i),'other',0,'x')
        with self.assertRaisesRegex(StorageStop,'CLOSING_RESERVE'):q.record('close','other',0,'x')
        q.closing=True;q.record('close','other',0,'x')
    def test_state_and_bundle_overflow(self):
        for kind in ['state','bundle']:
            with self.assertRaises(StorageStop):Store500().before('x',kind,LIMITS[kind][1]+1)

if __name__=='__main__':unittest.main()
