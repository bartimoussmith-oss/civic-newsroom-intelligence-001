from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import host_build

class HostBuildTests(unittest.TestCase):
    def fixture(self,root):
        dataset=root/'input';dataset.mkdir();(dataset/'published.json').write_text(json.dumps({'dataset_revision':'fixture','manifest_sha256':'fixture'}))
        text='Minutes\n---\n\nCouncil approved annexation.\n\nThe city shall pay $12.00.\n'
        record={'id':'fixture','title':'Fixture minutes','path':'meetings/fixture.md','version':sha256(text.encode()).hexdigest(),'text':text,'source':{},'dataset_revision':'fixture'}
        return dataset,record
    def test_complete_build_and_late_size_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);dataset,record=self.fixture(root);original=host_build.engine.build
            def completed_then_guard(records,out,revision):
                original(records,out,revision)
                raise ValueError('Intelligence file needs further partitioning')
            with patch.object(host_build.engine,'load',return_value=iter([record])),patch.object(host_build.engine,'build',side_effect=completed_then_guard):
                report=host_build.build_release(dataset,root/'output',1)
            self.assertEqual(report['records'],1)
            self.assertEqual(report['storage_policy']['derived_budget_bytes'],512*1024*1024)
            self.assertEqual(report['previous_size_guard'],'Intelligence file needs further partitioning')
            self.assertEqual(host_build.verify(root/'output/public')['records'],1)
            with patch.object(host_build,'BUDGET',1):
                with self.assertRaises(ValueError):host_build.verify(root/'output/public')
    def test_bad_input_is_not_recovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);dataset,record=self.fixture(root);record['version']='0'*64
            with patch.object(host_build.engine,'load',return_value=iter([record])):
                with self.assertRaisesRegex(ValueError,'Input text/hash mismatch'):host_build.build_release(dataset,root/'output',1)

if __name__=='__main__':unittest.main()
