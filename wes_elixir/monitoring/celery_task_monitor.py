from ast import literal_eval
from threading import Thread
from time import sleep

import wes_elixir.database.db_utils as db_utils


class TaskMonitor():
    '''Celery task monitor'''

    def __init__(self, celery_app, collection, timeout=0):
        '''Start celery task monitor daemon process'''

        self.celery_app = celery_app
        self.collection = collection
        self.timeout = timeout

        self.thread = Thread(target=self.run, args=())
        self.thread.daemon = True
        self.thread.start()


    def run(self):
        '''Daemon process for celery task monitor'''

        while True:

            try:

                with self.celery_app.connection() as connection:

                    listener = self.celery_app.events.Receiver(connection, handlers={
                        'task-failed'    : self.on_task_failed,
                        'task-received'  : self.on_task_received,
                        'task-revoked'   : self.on_task_revoked,
                        'task-started'   : self.on_task_started,
                        'task-succeeded' : self.on_task_succeeded
                    })
                    listener.capture(limit=None, timeout=None, wakeup=True)

            except (KeyboardInterrupt, SystemExit):
                raise

            except Exception as e:
                # TODO: implement better
                print(e)
                pass

            # Sleep for specified interval
            sleep(self.timeout)


    def on_task_failed(self, event):
        '''Event handler for failed (system error) celery tasks'''
        print("[TASK FAILED]", event)
        document = db_utils.update_run_state(self.collection, event['uuid'], 'SYSTEM_ERROR')


    def on_task_received(self, event):
        '''Event handler for received celery tasks'''
        print("[TASK RECEIVED]", event)
        document = db_utils.update_run_state(self.collection, event['uuid'], 'QUEUED')


    def on_task_revoked(self, event):
        '''Event handler for revoked celery tasks'''
        print("[TASK REVOKED]", event)
        document = db_utils.update_run_state(self.collection, event['uuid'], 'CANCELED')


    def on_task_started(self, event):
        '''Event handler for started celery tasks'''
        print("[TASK STARTED]", event)
        document = db_utils.update_run_state(self.collection, event['uuid'], 'RUNNING')


    def on_task_succeeded(self, event):
        '''Event handler for successful and failed (executor error) celery tasks'''
        result = literal_eval(event['result'])
        if result['returncode']:
            print("[TASK FAILED]", event)
            document = db_utils.update_run_state(self.collection, event['uuid'], 'EXECUTOR_ERROR')
        else:
            print("[TASK SUCCEEDED]", event)
            document = db_utils.update_run_state(self.collection, event['uuid'], 'COMPLETE')
        print(document)
