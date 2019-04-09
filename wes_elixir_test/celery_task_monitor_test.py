
import unittest
from wes_elixir.tasks.celery_task_monitor import cwl_tes_outputs_parser



def parseOutputs(filename):
    
    with open(filename) as f:
        
        log = f.read()
        
    return cwl_tes_outputs_parser(log)


class CeleryTaskMonitorTest(unittest.TestCase):


    def test_parse_Maxim_output(self):
        
        outputs = parseOutputs('wes_elixir_test/resources/Maxim_output.txt')
        
        print(outputs)
        
        self.assertEquals(outputs, {})   # FIXME
            
            
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
            
            
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()