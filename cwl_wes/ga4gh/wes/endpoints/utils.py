import os
import re

from werkzeug.exceptions import BadRequest

from cwl_wes.config.app_config import parse_app_config
from drs_cli.client import DRSClient
from foca.config.config_parser import get_conf
from flask import current_app


from typing import Dict

_RE_DOMAIN_PART = r'[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?'
_RE_DOMAIN = rf"({_RE_DOMAIN_PART}\.)+{_RE_DOMAIN_PART}\.?"
_RE_DRS_ID = r'.+'
_RE_OBJECT_ID = rf"(^(drs:\/\/{_RE_DOMAIN}\/)?(?P<obj_id>{_RE_DRS_ID})$)"

# def replace_drs_uris(data: Dict) -> None:
#     """TODO: Write Docs"""
#     # Iterate through the keys, perform regex and replace it with ftp values
#     for key in data:
#         match = re.search(_RE_OBJECT_ID, data[key], re.I)
#         if match:
#             access_url = get_url_for_drs_id(data[key])
#             data[key] = access_url



def get_url_for_drs_id(uri: str) -> str:
    """TODO: Write docs"""
    config = current_app.config
    supported_access_methods = get_conf(config, 'service_info', 'supported_access_methods')
    client =  DRSClient(uri)
    drs_object = client.get_object(uri)
    url = ""
    try:
        access_methods = drs_object['access_methods']
        url_found = False
        for method in supported_access_methods:
            for access_method in access_methods:
                if access_method['type'] == method:
                    try:
                        access_url = access_method['access_url']
                        url = access_url['url']
                        url_found = True
                        break
                    except KeyError:
                        continue
            if url_found:
                break
    except (KeyError, BadRequest):
        raise BadRequest("No access methods found")


    if url_found:
        return url
    else:
        raise BadRequest("No access method found")



def __translate_drs_uris_to_access_links(path: str) -> None:
    """
    The file path is in document['internal']['param_file_path'] and,
    all other files will be under document['internal']['cwl_path'])
    (document is the name of the container object in the context of 
    __create_run_environment(), inside __process_workflow_attachments() it's called data)
    """
    for dir in os.listdir(path):
        if os.path.isdir(os.path.join(path, dir)):
            __translate_drs_uris_to_access_links(os.path.join(path, dir))
        else:       
            try:
                file_abs_path = os.path.join(path, dir)
                my_file = open(file_abs_path)
                content = my_file.read()
                content_new = re.sub(_RE_OBJECT_ID, replace_drs_uri , content)
                my_file.close()
                a_file = open(file_abs_path, "w")
                a_file.write(content_new)
            except Exception as e:
                print(e)
                # Log exception and remove print
                

def replace_drs_uri(matchObj):
    """TODO: Write docs"""
    access_url = get_url_for_drs_id(matchObj.group(0))
    return access_url



