
import unittest
from wes_elixir.config.app_config import parse_app_config
from wes_elixir.config.config_parser import get_conf_type
from wes_elixir.factories.connexion_app import create_connexion_app
from wes_elixir.database.register_mongodb import \
    create_mongo_client, getMongoUri
from flask_pymongo import PyMongo
from unittest.mock import patch
from wes_elixir.ga4gh.wes.endpoints.run_workflow import __run_workflow as run_workflow


TES_URL = 'https://csc-tesk.c03.k8s-popup.csc.fi/'


class Test(unittest.TestCase):


    def test_get_conf_type(self):
        
        # Parse app configuration
        config = parse_app_config(config_var='WES_CONFIG')
        
        specs = get_conf_type(config, 'api', 'specs', types=(list))
        

    def test_create_mongo_client(self):
        
        # Parse app configuration
        config = parse_app_config(config_var='WES_CONFIG')
    
        # Create Connexion app
        connexion_app = create_connexion_app(config)
    
        app = connexion_app.app
        
        create_mongo_client(app, app.config)

        
    def test_remote_storage_url_should_be_optional(self):
        
        # Parse app configuration
        config = parse_app_config(config_var='WES_CONFIG')
        
        # *With* 'remote_storage_url'--------------------------------------------------------------------------
        
        config.storage['remote_storage_url'] = 'ftp://remote.storage'
        
        self.assertCmdList(config, [
            
            'cwl-tes',
            '--debug',
            '--leave-outputs',
            '--remote-storage-url', 'ftp://remote.storage',
            '--tes',
            TES_URL,
            'cwl_path',
            'param_file_path'
        ])
        
        
        # *Without* -------------------------------------------------------------------------------------------
        
        # Deleting remote_storage_url
        config.storage.pop('remote_storage_url')
        
        self.assertFalse('remote_storage_url' in config.storage)
        
        self.assertCmdList(config, [
            
            'cwl-tes',
            '--debug',
            '--leave-outputs',
            '--tes',
            TES_URL,
            'cwl_path',
            'param_file_path'
        ])
        
        
    @patch('wes_elixir.tasks.tasks.run_workflow.task__run_workflow.apply_async')        
    def assertCmdList(self, config, expectedCmdList, applyAsyncMock):

        '''
        run_id =           document['run_id']
        task_id =          document['task_id']
        tmp_dir =          document['internal']['tmp_dir']
        cwl_path =         document['internal']['cwl_path']
        param_file_path =  document['internal']['param_file_path']
        '''
        run_workflow(config, {
            
             'run_id'   : 'run_id'
            ,'task_id'  : 'task_id'
            ,'internal' : {

                 'tmp_dir'         : 'tmp_dir'
                ,'cwl_path'        : 'cwl_path'
                ,'param_file_path' : 'param_file_path'
            }
        })
        
        calls = applyAsyncMock.mock_calls
        print(calls)
        '''
        [call(None, { 'command_list'   : ['cwl-tes', '--debug', '--leave-outputs', '--remote-storage-url', None, '--tes', 'http://192.168.99.100:31567', 'cwl_path', 'param_file_path']
                    , 'tmp_dir'        : 'tmp_dir'
                    }
                    , soft_time_limit    = None
                    , task_id            = 'task_id'
             )]
        '''

        self.assertTrue(len(calls) == 1)
        
        call = calls[0]
        
        self.assertEquals( call[1][1]['command_list'], expectedCmdList)


#     @patch.dict('os.environ', {'MONGO_HOST': ':'})  # Error!!!
#     @patch.dict('os.environ', {'MONGO_USERNAME': 'tfga:'})  # Different error (Username and password must be escaped according to RFC 3986, use urllib.parse.quote_plus().)
    def test_getMongoUri(self):
        '''
        Trying to reproduce this error:


        C02X83UXJHD2:HDR dolphy$ kubectl logs -f wes-elixir-dev-696cb447d5-dg7vq
        [2019-02-13 13:44:44,277: INFO    ] Logging config loaded from '/app/wes_elixir/config/log_config.yaml'. [wes_elixir.config.log_config]
        [2019-02-13 13:44:44,291: INFO    ] App config loaded from '/app/wes_elixir/config/app_config.yaml'. [wes_elixir.config.app_config]
        [2019-02-13 13:44:44,393: INFO    ] Connexion app created from '/app/wes_elixir/app.py:run_server'. [wes_elixir.factories.connexion_app]
        [2019-02-13 13:44:44,443: INFO    ] Connexion app configured. [wes_elixir.factories.connexion_app]
        Traceback (most recent call last):
         File "/app/wes_elixir/app.py", line 52, in <module>
           connexion_app, config = run_server()
         File "/app/wes_elixir/app.py", line 26, in run_server
           connexion_app.app = register_mongodb(connexion_app.app)
         File "/app/wes_elixir/database/register_mongodb.py", line 26, in register_mongodb
           config=config,
         File "/app/wes_elixir/database/register_mongodb.py", line 82, in create_mongo_client
           mongo = PyMongo(app)
         File "/usr/local/lib/python3.6/site-packages/flask_pymongo/__init__.py", line 116, in __init__
           self.init_app(app, uri, *args, **kwargs)
         File "/usr/local/lib/python3.6/site-packages/flask_pymongo/__init__.py", line 149, in init_app
           parsed_uri = uri_parser.parse_uri(uri)
         File "/usr/local/lib/python3.6/site-packages/pymongo/uri_parser.py", line 424, in parse_uri
           nodes = split_hosts(hosts, default_port=default_port)
         File "/usr/local/lib/python3.6/site-packages/pymongo/uri_parser.py", line 260, in split_hosts
           nodes.append(parse_host(entity, port))
         File "/usr/local/lib/python3.6/site-packages/pymongo/uri_parser.py", line 147, in parse_host
           raise ValueError("Reserved characters such as ':' must be "
        ValueError: Reserved characters such as ':' must be escaped according RFC 2396. An IPv6 address literal must be enclosed in '[' and ']' according to RFC 2732.
        '''
        
        # Parse app configuration
        config = parse_app_config(config_var='WES_CONFIG')
    
        # Create Connexion app
        connexion_app = create_connexion_app(config)

        app = connexion_app.app

        mongoUri = getMongoUri(config)
        app.config['MONGO_URI'] = mongoUri
        
        print(mongoUri)
    
        PyMongo(app)


        
        
        
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()