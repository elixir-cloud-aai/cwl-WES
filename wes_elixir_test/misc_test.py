
import unittest
from wes_elixir.config.app_config import parse_app_config
from wes_elixir.config.config_parser import get_conf_type
from wes_elixir.factories.connexion_app import create_connexion_app
from wes_elixir.database.register_mongodb import \
    create_mongo_client, getMongoUri
from flask_pymongo import PyMongo
from unittest.mock import patch


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