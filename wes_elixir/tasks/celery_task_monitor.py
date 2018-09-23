from ast import literal_eval
import logging
from threading import Thread
from time import sleep

import wes_elixir.database.db_utils as db_utils


# Get logger instance
logger = logging.getLogger(__name__)


class TaskMonitor():
    '''Celery task monitor'''

    def __init__(self, celery_app, collection, timeout=0):
        '''Start Celery task monitor daemon process'''

        self.celery_app = celery_app
        self.collection = collection
        self.timeout = timeout

        self.thread = Thread(target=self.run, args=())
        self.thread.daemon = True
        self.thread.start()

        logger.debug("Celery task monitor daemon process started...")


    def run(self):
        '''Daemon process for Celery task monitor'''

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

        logger.warning("Celery task monitor daemon process shut down!")


    def on_task_failed(self, event):
        '''Event handler for failed (system error) Celery tasks'''
        state='SYSTEM_ERROR'
        #print("[TASK FAILED]", event)
        document = db_utils.update_run_state(self.collection, event['uuid'], state)
        logger.info("State of run '{run_id}' (task id: {task_id}) changed to '{state}'".format(
            run_id=document['run_id'],
            task_id=event['uuid'],
            state=state,
        ))

    def on_task_received(self, event):
        '''Event handler for received Celery tasks'''
        state='QUEUED'
        #print("[TASK RECEIVED]", event)
        document = db_utils.update_run_state(self.collection, event['uuid'], state)
        logger.info("State of run '{run_id}' (task id: {task_id}) changed to '{state}'".format(
            run_id=document['run_id'],
            task_id=event['uuid'],
            state=state,
        ))


    def on_task_revoked(self, event):
        '''Event handler for revoked Celery tasks'''
        state='CANCELED'
        #print("[TASK REVOKED]", event)
        document = db_utils.update_run_state(self.collection, event['uuid'], state)
        logger.info("State of run '{run_id}' (task id: {task_id}) changed to '{state}'".format(
            run_id=document['run_id'],
            task_id=event['uuid'],
            state=state,
        ))


    def on_task_started(self, event):
        '''Event handler for started Celery tasks'''
        state='RUNNING'
        #print("[TASK STARTED]", event)
        document = db_utils.update_run_state(self.collection, event['uuid'], state)
        logger.info("State of run '{run_id}' (task id: {task_id}) changed to '{state}'".format(
            run_id=document['run_id'],
            task_id=event['uuid'],
            state=state,
        ))


    def on_task_succeeded(self, event):
        '''Event handler for successful and failed (executor error) Celery tasks'''
        #print("[TASK FINISHED]", event)
        result = literal_eval(event['result'])
        if result['returncode']:
            state='EXECUTOR_ERROR'
            document = db_utils.update_run_state(self.collection, event['uuid'], state)
            logger.info("State of run '{run_id}' (task id: {task_id}) changed to '{state}'".format(
                run_id=document['run_id'],
                task_id=event['uuid'],
                state=state,
            ))
        else:
            state='COMPLETE'
            document = db_utils.update_run_state(self.collection, event['uuid'], state)
            logger.info("State of run '{run_id}' (task id: {task_id}) changed to '{state}'".format(
                run_id=document['run_id'],
                task_id=event['uuid'],
                state=state,
            ))