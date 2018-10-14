"""Functions to be executed in background and related utility functions."""

import logging
import re
import subprocess

from wes_elixir.celery_worker import celery


# Get logger instance
logger = logging.getLogger(__name__)


@celery.task(bind=True, track_started=True)
def task__run_workflow(
    self,
    command_list,
    tmp_dir
):
    """Adds workflow run to task queue."""

    # Execute task in background
    proc = subprocess.Popen(
        command_list,
        cwd=tmp_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )

    # Parse output in real-time
    log, tes_ids = __process_cwl_logs(self, stream=proc.stdout)

    returncode = proc.wait()

    return (returncode, log, tes_ids)


def __process_cwl_logs(task, stream):
    """Parses combinend cwl-tes STDOUT/STDERR and sends TES task IDs and state
    updates to broker."""

    stream_container = list()
    tes_states = dict()

    # Iterate over STDOUT/STDERR stream
    for line in iter(stream.readline, ''):

        line = line.rstrip()

        # Handle special cases
        lines = __handle_cwl_tes_log_irregularities(line)
        for line in lines:
            stream_container.append(line)
            logger.info(line)
            continue

        # Detect TES task state changes
        (tes_id, tes_state) = __extract_tes_task_state_from_cwl_tes_log(line)
        if tes_id:

            # Handle new task
            if tes_id not in tes_states:
                tes_states[tes_id] = tes_state
                __send_event_tes_task_update(
                    task,
                    tes_id=tes_id,
                )
            # Handle state change
            elif tes_states[tes_id] != tes_state:
                tes_states[tes_id] = tes_state
                __send_event_tes_task_update(
                    task,
                    tes_id=tes_id,
                    tes_state=tes_state,
                )
            logger.info(line)
            continue

        stream_container.append(line)
        logger.info(line)

    return (stream_container, list(tes_states.keys()))


def __handle_cwl_tes_log_irregularities(line):
    """Handles irregularities arising from log parsing."""

    lines = list()

    # Handle special case where FTP and cwl-tes logs are on same line
    re_ftp_cwl_tes = re.compile(
        r'^(\*cmd\* .*)(\[step \w*\] produced output \{)$'
    )
    m = re_ftp_cwl_tes.match(line)
    if m:
        lines.append(m.group(1))

    return lines


def __extract_tes_task_state_from_cwl_tes_log(line):
    """Extracts task ID and state from cwl-tes log."""

    task_id = None
    task_state = None

    # Extract new task ID
    re_task_new = re.compile(r"^\[job \w*\] task id: (\S*)$")
    m = re_task_new.match(line)
    if m:
        task_id = m.group(1)

    # Extract task ID and state
    re_task_state_poll = re.compile(
        r"^\[job \w*\] POLLING '(\S*)', result: (\w*)"
    )
    m = re_task_state_poll.match(line)
    if m:
        task_id = m.group(1)
        task_state = m.group(2)

    return (task_id, task_state)


def __send_event_tes_task_update(
    task,
    tes_id,
    tes_state=None
):
    """Sends custom event to inform about TES task state change."""

    task.send_event(
        'task-tes-task-update',
        tes_id=tes_id,
        tes_state=tes_state,
    )
