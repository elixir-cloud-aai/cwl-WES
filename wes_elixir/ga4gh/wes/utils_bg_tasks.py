from wes_elixir.celery_worker import celery


@celery.task(bind=True)
def sleep_a_bit(self, sec):
    import time
    time.sleep(sec)


@celery.task(bind=True, track_started=True)
def add_run_to_task_queue(self, run_dir, tes, cwl, params):
    '''Adds workflow run to task queue'''

    # TODO: Placeholder until TESK is fixed
    print("STARTING BACKGROUND TASK")
    print("Run directory:", run_dir)
    import time
    time.sleep(5)
    print("FINISHED BACKGROUND TASK")

    # TODO: Uncomment when TESK is back up again
    ## Build command
    #command = [
    #    "cwl-tes",
    #    "--tes",
    #    tes,
    #    cwl,
    #    params
    #]
    #
    ## Execute command
    # TODO: Use Popen instead
    #subprocess.run(command)
