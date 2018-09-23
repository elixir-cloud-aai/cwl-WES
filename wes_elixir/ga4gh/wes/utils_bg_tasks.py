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
        # TODO: Capture stdout/stderr
        # TODO: Ensure they're captured as or converted to string not byte
        # TODO: Ensure they are wrapped properly for long strings ("""?""")
        #stdout=subprocess.PIPE,
        #stderr=subprocess.PIPE,
        #universal_newlines=True
        # TODO: Use this from Python 3.7 on instead of stdout & stderr
        #capture_output=True
    )

    # Return returncode, stdout, stderr and command args as dictionary
    return vars(bg_proc)
