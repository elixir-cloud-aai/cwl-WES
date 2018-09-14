from wes_elixir.celery_worker import celery


@celery.task(bind=True)
def sleep_a_bit(self, sec):
    import time
    time.sleep(sec)


@celery.task(bind=True, track_started=True)
def add_run_to_task_queue(self, config, command_list):
    '''Adds workflow run to task queue'''

    # TODO: Placeholder until TESK is fixed
    print("STARTING BACKGROUND TASK")
    #print("Run directory:", run_dir)
    #import time

    import subprocess

    bg_proc = subprocess.run(
            command_list
        )

    print(vars(bg_proc))

    print("FINISHED BACKGROUND TASK")

    # TODO: Uncomment when TESK is back up again
    ## Build command
    #
    ## Execute command
    # TODO: Use Popen instead
    #subprocess.run(command)

