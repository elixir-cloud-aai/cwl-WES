from app import config, db_runs, service_info
from connexion import request


class server:
    '''Controllers for the GA4GH WES API endpoints'''

    def CancelRun(self, **kwargs):
        return {}


    def GetRunLog(self, **kwargs):
        return {}


    def GetRunStatus(self, **kwargs):
        return {}


    def GetServiceInfo():
        '''Return service info'''
        # TODO: Handle errors
        response = service_info.get_service_info()
        return response


    def ListRuns(self, page_size, page_token, **kwargs):
        ''''''
        return {}


    def RunWorkflow(self, **kwargs):
        return {}
