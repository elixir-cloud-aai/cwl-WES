from connexion import request

import wes_elixir.ga4gh.wes.utils_runs as runs
import wes_elixir.ga4gh.wes.utils_service_info as service_info


# INITIALIZE SERVICE INFO
service_info.get_service_info(silent=True)


# ROUTES FOR WES ENDPOINTS
def CancelRun(run_id):
    '''Cancel unfinished workflow run'''
    return {"run_id": runs.cancel_run(run_id)}


def GetRunLog(run_id):
    '''Return detailed run info'''
    return runs.get_run_log(run_id)


def GetRunStatus(run_id):
    '''Return run status'''
    return runs.get_run_status(run_id)


def GetServiceInfo():
    '''Return service info'''
    return service_info.get_service_info()


def ListRuns(**kwargs):
    '''List ids and status of all workflow runs'''
    return runs.list_runs(**kwargs)


def RunWorkflow():
    '''Execute workflow'''
    return {"run_id": runs.run_workflow(request.form)}
