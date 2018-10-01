import json
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

    # Squash relevant results into single string
    # NOTE: Hack to get around serialization/deserialization problem
    stdout = '<<<newline>>>'.join(bg_proc.stdout.splitlines())
    stderr = '<<<newline>>>'.join(bg_proc.stderr.splitlines())
    result = '<<<newfield>>>'.join([str(bg_proc.returncode), stdout, stderr])

    # Return result
    return result