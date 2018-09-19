import subprocess

from wes_elixir.celery_worker import celery


@celery.task(bind=True, track_started=True)
def add_command_to_task_queue(self, command_list, tmp_dir):
    '''Adds workflow run to task queue'''

    # Execute task in background
    bg_proc = subprocess.run(
        command_list,
        cwd=tmp_dir
    )

    # Return returncode, stdout, stderr and command args as dictionary
    return vars(bg_proc)
