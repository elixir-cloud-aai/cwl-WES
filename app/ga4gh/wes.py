from app import runs, service_info
from connexion import request


class server:
    '''Controllers for the GA4GH WES API endpoints'''

    def CancelRun(run_id):
        '''Cancel unfinished workflow run'''
        # TODO: Handle errors
        return {"run_id": runs.cancel_run(run_id)}


    def GetRunLog(run_id):
        '''Return detailed run info'''
        # TODO: Handle errors
        return runs.get_run_log(run_id)


    def GetRunStatus(run_id):
        '''Return run status'''
        # TODO: Handle errors
        return runs.get_run_status(run_id)


    def GetServiceInfo():
        '''Return service info'''
        # TODO: Handle errors
        return service_info.get_service_info()


    def ListRuns(page_size, page_token):
        '''List ids and status of all workflow runs'''
        # TODO: Handle errors
        return runs.list_runs(page_size)


    def RunWorkflow():
        '''Execute workflow'''
        # TODO: Handle errors
        return {"run_id": runs.run_workflow(request.form)}
