
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
            
            
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()