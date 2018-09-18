from threading import Thread
from time import sleep

import wes_elixir.database.utils as db_utils


class TaskMonitor():
    '''Celery task monitor'''

    def __init__(self, celery_app, connexion_app, timeout=0.05):
        '''Start celery task monitor daemon process'''

        self.celery_app = celery_app
        self.connexion_app = connexion_app
        self.timeout = timeout

        self.thread = Thread(target=self.run, args=())
        self.thread.daemon = True
        self.thread.start()


    def run(self):
        '''Daemon process for celery task monitor'''

        while True:

            try:

                with self.celery_app.connection() as connection:

                    recv = self.celery_app.events.Receiver(connection, handlers={
                        #'*' : self.catchall
                        'task-failed'    : self.on_task_failed,
                        'task-received'  : self.on_task_received,
                        'task-revoked'   : self.on_task_revoked,
                        'task-started'   : self.on_task_started,
                        'task-succeeded' : self.on_task_succeeded
                    })
                    recv.capture(limit=None, timeout=None, wakeup=True)

            except (KeyboardInterrupt, SystemExit):
                raise

            except Exception as e:
                # TODO: implement better
                pass

            # Sleep for specified interval
            sleep(self.timeout)


    def on_task_failed(self, event):
        '''Event handler for failed celery tasks'''
        print("SAFASFDASFASF")
        document = db_utils.update_run_state(collection_runs, run_id, "EXECUTOR_ERROR")
        print("[TASK FAILED]", event)
        print(document)


    def on_task_received(self, event):
        print("SAFASFDASFASF")
        '''Event handler for received celery tasks'''
        document = db_utils.update_run_state(collection_runs, run_id, "QUEUED")
        print("[TASK RECEIVED]", event)
        print(document)


    def on_task_revoked(self, event):
        print("SAFASFDASFASF")
        '''Event handler for revoked celery tasks'''
        document = db_utils.update_run_state(collection_runs, run_id, "CANCELED")
        print("[TASK REVOKED]", event)
        print(document)


    def on_task_started(self, event):
        print("SAFASFDASFASF")
        '''Event handler for started celery tasks'''
        document = db_utils.update_run_state(collection_runs, run_id, "RUNNING")
        print("[TASK STARTED]", event)
        print(document)


    def on_task_succeeded(self, event):
        print("SAFASFDASFASF")
        '''Event handler for succeeded celery tasks'''
        document = db_utils.update_run_state(collection_runs, run_id, "COMPLETE")
        print("[TASK SUCCEEDED]", event)
        print(document)

    def catchall(self, event):
        if event['type'] != 'worker-heartbeat':
            print(event)
