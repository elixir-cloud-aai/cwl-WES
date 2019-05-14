
import unittest
from wes_elixir.tasks.celery_task_monitor import cwl_tes_outputs_parser
from pprint import pprint



def parseOutputs(filename):
    
    with open(filename) as f:
        
        log = f.read()
        
    return cwl_tes_outputs_parser(log)


class CeleryTaskMonitorTest(unittest.TestCase):


    def test_parse_Maxim_output(self):
        
        outputs = parseOutputs('wes_elixir_test/resources/Maxim_output.txt')
        
        pprint(outputs)
        
        self.assertEquals(outputs, {
            
            "cmsearch_matches": [
                {
                    "location": "file:///data/tmp/YYERT8/tmp8e8rmrys/mrum-genome.fa.cmsearch_matches.tbl",
                    "basename": "mrum-genome.fa.cmsearch_matches.tbl",
                    "class": "File",
                    "checksum": "sha1$98248e0b675e90b31d93847b5991589cb921c340",
                    "size": 8236,
                    "path": "/data/tmp/YYERT8/tmp8e8rmrys/mrum-genome.fa.cmsearch_matches.tbl"
                },
                {
                    "location": "file:///data/tmp/YYERT8/tmpesf5g3nn/mrum-genome.fa.cmsearch_matches.tbl",
                    "basename": "mrum-genome.fa.cmsearch_matches.tbl",
                    "class": "File",
                    "checksum": "sha1$b02cf868bd19a9c7e4a0b06fab7a2ac1c223d219",
                    "size": 1176,
                    "path": "/data/tmp/YYERT8/tmpesf5g3nn/mrum-genome.fa.cmsearch_matches.tbl"
                }
            ],
            "concatenate_matches": {
                "location": "file:///data/tmp/YYERT8/tmpnwuwklm8/cat_cmsearch_matches.tbl",
                "basename": "cat_cmsearch_matches.tbl",
                "class": "File",
                "checksum": "sha1$697e703df0c489b201febd08dafd26d6ebb59a41",
                "size": 9412,
                "path": "/data/tmp/YYERT8/tmpnwuwklm8/cat_cmsearch_matches.tbl"
            },
            "deoverlapped_matches": {
                "location": "file:///data/tmp/YYERT8/tmpkf4u0p4r/cat_cmsearch_matches.tbl.deoverlapped",
                "basename": "cat_cmsearch_matches.tbl.deoverlapped",
                "class": "File",
                "checksum": "sha1$4d88865ee67b33fbf3db268a211fce9dbff715dd",
                "size": 7490,
                "path": "/data/tmp/YYERT8/tmpkf4u0p4r/cat_cmsearch_matches.tbl.deoverlapped"
            }
        })
            
            
    def test_parse_HashSplitter_output(self):
        
        outputs = parseOutputs('wes_elixir_test/resources/HashSplitter_output.txt')
        
        print(outputs)
        
        self.assertEquals(outputs, {
            
            'output': {
                
                'basename': 'unify',
                'checksum': 'sha1$fa6af7f4f7fa2fe5b6734c670ee73253e415dd4d',
                'class': 'File',
                'location': 'file:///data/tmp/W7OAI8/tmpuwmrjrs5/unify',
                'path': '/data/tmp/W7OAI8/tmpuwmrjrs5/unify',
                'size': 413
            }
        })
    def test_parse_failed_output(self):
        outputs = parseOutputs('wes_elixir_test/resources/failed_output.txt')
        print(outputs)
        self.assertEquals(outputs, {
         'output': None
        })
            
            
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
