"""Pure adapter fixtures. No environment/model imports or execution."""
import hashlib
import json
import tempfile
import types
import unittest
from pathlib import Path
from retry.io501 import Adapter501,AdapterStop
from retry.storage500 import Store500,StorageStop
from retry.pilot420_json import json_ready,restore_bytes


def fake_runtime():
    def plainread(path):return json.loads(Path(path).read_text())
    def plainsave(path,value):raise AssertionError('UNROUTED_WRITER')
    def receipt(path,value):raise AssertionError('UNROUTED_RECEIPT')
    def load(path):return restore_bytes(plainread(path))
    def canonical(value):return hashlib.sha256(json.dumps(json_ready(value),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    def mod(name,**attrs):return types.SimpleNamespace(__name__='retry492.'+name,__private_clone492__=True,**attrs)
    codec=mod('io481',ORIGINAL_READ=plainread,ORIGINAL_LOAD=load,read=plainread,load_receipt=load,
        json_ready=json_ready,restore_bytes=restore_bytes,canonical=canonical,
        STATE_KEY='__haic_full_state_ref481__',CODEC_KEY='__haic_lossless481__')
    modules={'io481':codec,'loss389_analyze':mod('loss389_analyze',save=plainsave,read=plainread,sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()),
        'receipt421_io':mod('receipt421_io',save_receipt=receipt,load_receipt=load),
        'consumer':mod('consumer',save=plainsave,save_receipt=receipt,read=plainread,load_receipt=load)}
    return types.SimpleNamespace(modules=modules,import_module=lambda name:modules[name])


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)
        self.store=Store500(self.base/'raw');self.runtime=fake_runtime()
        self.adapter=Adapter501(self.runtime,self.store).install()
    def tearDown(self):self.temp.cleanup()
    def test_aliases_roundtrip_and_late_writer(self):
        m=self.runtime.modules['consumer'];path=self.store.root/'receipt.json'
        value={'binary':b'\0\xff','nested':{'x':-0.0}}
        digest=m.save_receipt(path,value)
        self.assertEqual(digest,self.adapter.codec.canonical(value));self.assertEqual(m.load_receipt(path),value)
        self.assertFalse(path.exists());self.assertTrue(Path(self.adapter.physical_ref(path)['path']).exists())
        self.assertEqual(self.adapter.codec.read(path),value)
        self.assertEqual(self.runtime.modules['loss389_analyze'].sha(path),self.adapter.physical_ref(path)['sha256'])
        self.assertTrue(self.adapter.audit()['passed'])
        late=types.SimpleNamespace(__name__='retry492.late',__private_clone492__=True,save=self.adapter.original_save)
        self.runtime.modules['late']=late;self.adapter.install()
        late.save(self.store.root/'late.json',{'ok':True});self.assertEqual(self.adapter.read(self.store.root/'late.json'),{'ok':True})
    def test_versions_and_identical_plain_coalesce(self):
        p=self.store.root/'budget.json';a=self.adapter
        a.save(p,{'n':1});first=a.physical_ref(p);used=len(self.store.used)
        a.save(p,{'n':1});self.assertEqual(len(self.store.used),used)
        a.save(p,{'n':2});self.assertNotEqual(a.physical_ref(p)['path'],first['path'])
        self.assertTrue(Path(first['path']).exists());self.assertEqual(a.read(p),{'n':2})
    def test_state_intern_and_tamper(self):
        state=dict(physical={'x':1.},finish_tracker={'candidate':None},elapsed_raw_steps=1)
        a=self.adapter;p=self.store.root/'a.json';q=self.store.root/'b.json'
        a.save_receipt(p,{'state':state,'bytes':b'492'});a.save_receipt(q,{'state':state})
        self.assertEqual(self.store.counts['state'],1);self.assertEqual(a.read(p)['state'],state)
        path=next(self.store.root.glob('state-*.json'));path.write_bytes(b'{}')
        with self.assertRaises(AdapterStop):a.read(p)
    def test_final_serialized_bundle_cap_and_missing_writer(self):
        before=len(self.store.used)
        with self.assertRaises(StorageStop):self.adapter.writer(self.store.root/'x-bundle.json',{'text':'x'*(64*1024)},kind='bundle')
        self.assertEqual(len(self.store.used),before)
        with self.assertRaises(FileNotFoundError):self.adapter.read(self.store.root/'unwritten.json')
        foreign=types.SimpleNamespace(__name__='retry.foreign',save=self.adapter.original_save)
        self.runtime.modules['foreign']=foreign
        with self.assertRaises(AdapterStop):self.adapter.install()
    def test_immutable_receipt_and_registered_write_root(self):
        p=self.store.root/'once.json';self.adapter.save_receipt(p,{'n':1})
        with self.assertRaises(AdapterStop):self.adapter.save_receipt(p,{'n':2})
        with self.assertRaises(AdapterStop):self.adapter.save(self.base/'outside.json',{})
    def test_old481_state_refs_use_source_directory(self):
        a=self.adapter;old=self.base/'old481';old.mkdir()
        state=dict(physical={'old':42},finish_tracker={},elapsed_raw_steps=9)
        h=a.codec.canonical(state)
        (old/('state-'+h+'.json')).write_bytes(a.encode(dict(full_state=state,sha256=h)))
        packed={a.codec.CODEC_KEY:1,'payload':{'root':{a.codec.STATE_KEY:h}},'decoded_sha256':a.codec.canonical({'root':state})}
        path=old/'receipt.json';path.write_bytes(a.encode(packed))
        self.assertEqual(a.read(path),{'root':state})
    def test_repeated_large_metadata_containers_are_interned(self):
        a=self.adapter;raw=[{'tick':i,'raw':('x'*1000)} for i in range(140)]
        first={'child_rows':raw,'other':{'all_fields':[1,None,True,b'bytes']}}
        second={'stream_actions':{'frozen_row':raw},'observer_posts':raw}
        a.save(self.store.root/'child.json',first);a.save(self.store.root/'observer.json',second)
        self.assertEqual(a.read(self.store.root/'child.json'),first)
        self.assertEqual(a.read(self.store.root/'observer.json'),second)
        objects=list(self.store.root.glob('content501-*.json'))
        self.assertEqual(len(objects),1)
        self.assertLess(sum(self.store.sizes.values()),len(a.encode(raw))+4096)
    def test_distinct_ten_k_rows_do_not_explode_file_count(self):
        #64 distinct10KiB rows are a bounded representative structural fixture.
        # Rows are below the fixed128KiB threshold, so448 such rows create no
        # individual objects; a full4.5MiB list splits into at most5chunks.
        rows=[{'ordinal':i,'raw':'x'*(10*1024)} for i in range(64)]
        value={'child_rows':rows,'observer_actions':{'frozen_rows':rows}}
        self.adapter.save(self.store.root/'distinct-rows.json',value)
        self.assertEqual(self.adapter.read(self.store.root/'distinct-rows.json'),value)
        self.assertEqual(len(list(self.store.root.glob('content501-*.json'))),1)
        self.assertEqual(len(self.store.used),2)
        self.assertLess(sum(self.store.sizes.values()),1024*1024)
    def test_direct_tick_bundle_never_use_generic_refs(self):
        from retry.io501 import CONTENT,CHUNKS
        for kind in ('tick','bundle'):
            p=self.store.root/(kind+'.json');ref=self.adapter.writer(p,{'text':'x'*9000},kind=kind)
            encoded=Path(ref['path']).read_text()
            self.assertNotIn(CONTENT,encoded);self.assertNotIn(CHUNKS,encoded)
    def test_chunked_observer_list_lossless(self):
        # About1.05MiB of newly generated payload, under2MiB derived fixture cap.
        value={'posts':['x'*4096 for _ in range(260)]}
        self.adapter.save(self.store.root/'observer-final.json',value)
        self.assertEqual(self.adapter.read(self.store.root/'observer-final.json'),value)
        self.assertLess(sum(self.store.sizes.values()),2*1024*1024)

if __name__=='__main__':unittest.main()
