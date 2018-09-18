import wes_elixir.database.utils as db_utils

from wes_elixir.celery_worker import celery


#@celery.task(bind=True, track_started=True)
#def add_run_to_task_queue(self, config, document, command_list, tmp_dir):
def add_run_to_task_queue(config, document, command_list, tmp_dir):
    '''Adds workflow run to task queue'''

    print(document)

    # Re-assign config values
    collection_runs = config['database']['collections']['runs']

    # Re-assign document values
    run_id = document['run_id']

    # Update run state to RUNNING
    document = db_utils.update_run_state(collection_runs, run_id, "RUNNING")

    print(document)
    print("STARTING BACKGROUND TASK")

    import subprocess

    #bg_proc = subprocess.run(
    bg_proc = subprocess.Popen(
            command_list
    )
    bg_proc.wait()

    if bg_proc.returncode == 0:
        # Update run state to COMPLETE
        document = db_utils.update_run_state(collection_runs, run_id, "COMPLETE")
    else:
        # Update run state to EXECUTOR_ERROR
        document = db_utils.update_run_state(collection_runs, run_id, "EXECUTOR_ERROR")

    print("FINISHED BACKGROUND TASK")
    print(document)
