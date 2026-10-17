"""Quota487 fixtures exercise real temporary files, never optimization/physics."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from retry.quota487 import Quota,QuotaStop,MIB

class Quota487Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='haic487-quota-test-')
        self.q=Quota(Path(self.temp.name)/'outputs',free_bytes=lambda _:4*1024**3)
    def tearDown(self):self.temp.cleanup()
    def test_contract_bounds(self):
        self.assertEqual((self.q.MAX_FILES,self.q.MAX_BYTES,self.q.FILE_BYTES,self.q.TEMP_BYTES),(32,8*MIB,2*MIB,2*MIB))
        self.assertEqual((self.q.CONTROL_FILES,self.q.CONTROL_BYTES,self.q.RESERVE_BYTES),(2,65536,512*MIB))
    def test_30_data_slots_leave_two_controls(self):
        for i in range(30):self.q.write_json(str(i)+'.json',{})
        with self.assertRaises(QuotaStop):self.q.write_json('overflow.json',{})
        self.assertFalse((self.q.directory/'overflow.json').exists())
        self.q.write_json('result.json',{},control=True);self.q.write_json('stop.json',{},control=True)
        self.assertEqual(self.q.inventory()['file_count'],32)
        with self.assertRaises(QuotaStop):self.q.write_json('stop-private.json',{},control=True)
    def test_data_bytes_cannot_spend_control_pool(self):
        # Smaller equivalent bounds test exact serialized sizes on disk.
        with patch.object(Quota,'MAX_BYTES',100),patch.object(Quota,'CONTROL_BYTES',20):
            self.q.write_json('data.json','x'*76) # JSON quotes+newline:79 bytes
            with self.assertRaises(QuotaStop):self.q.write_json('more.json',{})
            self.q.write_json('result.json','x'*17,control=True) #20 bytes
            self.assertEqual(self.q.inventory()['bytes'],99)
    def test_control_pool_is_bounded(self):
        with patch.object(Quota,'CONTROL_BYTES',8):
            with self.assertRaises(QuotaStop):self.q.write_json('result.json','x'*6,control=True)
        with self.assertRaises(QuotaStop):self.q.write_json('ordinary.json',{},control=True)
        self.assertEqual(self.q.inventory()['file_count'],0)
    def test_oversized_file_nan_and_paths_leave_no_output(self):
        with self.assertRaises(QuotaStop):self.q.write_json('huge.json','x'*(2*MIB))
        with self.assertRaises(ValueError):self.q.write_json('nan.json',float('nan'))
        for name in ('../outside.json','nested/file.json','/tmp/escape.json','x\\y.json','..'):
            with self.assertRaises(QuotaStop):self.q.write_json(name,{})
        self.assertEqual(self.q.inventory()['file_count'],0)
    def test_temp_and_disk_caps_precede_creation(self):
        with patch.object(Quota,'TEMP_BYTES',2):
            with self.assertRaises(QuotaStop):self.q.write_json('no.json',{})
        self.q.free_bytes=lambda _:512*MIB
        with self.assertRaises(QuotaStop):self.q.write_json('no.json',{})
        self.assertFalse((self.q.directory/'no.json').exists());self.assertEqual(self.q.temporary_bytes,0)
    def test_atomic_overwrite_and_exclusive_failure(self):
        self.q.write_json('journal.json',{'v':1});self.q.write_json('journal.json',{'v':2})
        with self.assertRaises(FileExistsError):self.q.write_json('journal.json',{},exclusive=True)
        self.assertEqual(json.loads((self.q.directory/'journal.json').read_text()),{'v':2})
        self.assertEqual(self.q.inventory()['file_count'],1);self.assertEqual(self.q.temporary_bytes,0)
        self.assertFalse(list(self.q.directory.glob('*.tmp')))
    def test_fsync_failure_cleans_transaction_without_replacing_old(self):
        self.q.write_json('journal.json',{'v':1});before=(self.q.directory/'journal.json').read_bytes()
        with patch('retry.quota487.os.fsync',side_effect=OSError('injected')):
            with self.assertRaises(OSError):self.q.write_json('journal.json',{'v':2})
        self.assertEqual((self.q.directory/'journal.json').read_bytes(),before)
        self.assertEqual(self.q.inventory()['file_count'],1);self.assertEqual(self.q.temporary_bytes,0)
    def test_external_mutation_and_untracked_output_fail_closed(self):
        self.q.write_json('data.json',{'v':1});p=self.q.directory/'data.json'
        p.write_bytes(p.read_bytes().replace(b'1',b'2')) # same size, digest changes
        with self.assertRaises(QuotaStop):self.q.write_json('next.json',{})
        with self.assertRaises(QuotaStop):self.q.inventory()
    def test_reopen_preserves_existing_inventory_and_termination_flags(self):
        self.q.write_json('data.json',{});self.q.write_json('result.json',{},control=True)
        reopened=Quota(self.q.directory,free_bytes=lambda _:4*1024**3)
        self.assertEqual(self.q.inventory(),reopened.inventory())

if __name__=='__main__':unittest.main()
