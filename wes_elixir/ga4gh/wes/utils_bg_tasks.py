import logging
import subprocess

from wes_elixir.celery_worker import celery


@celery.task(bind=True, track_started=True)
def add_command_to_task_queue(
    self,
    command_list,
    tmp_dir
):

    '''Adds workflow run to task queue'''

    # Execute task in background
    bg_proc = subprocess.run(
        command_list,
        cwd=tmp_dir,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # TODO: Use this from Python 3.7 on instead of stdout & stderr
        #capture_output=True
    )

    # Convert STDOUT and STDERR to lists of lines
    bg_proc.stdout = bg_proc.stdout.splitlines()
    bg_proc.stderr = bg_proc.stderr.splitlines()

    # Return returncode, stdout, stderr and command args as dictionary
    return vars(bg_proc)
