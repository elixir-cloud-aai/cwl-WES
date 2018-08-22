from app import config, db_runs, runs, service_info
from connexion import request


class server:
    '''Controllers for the GA4GH WES API endpoints'''

    def CancelRun():
        return {}


    def GetRunLog():
        return {}


    def GetRunStatus():
        return {}


    def GetServiceInfo():
        '''Return service info'''
        # TODO: Handle errors
        response = service_info.get_service_info()
        return response


    def ListRuns(page_size, page_token, **kwargs):
        ''''''
        return {}


    def RunWorkflow():
        '''Execute workflow'''
        payload_dict = dict()
        # TODO: handle 'multipart/form-data': save files, convert rest to dictionary
        response = runs.insert_workflow_run(payload_dict)
        return {"run_id": response}
