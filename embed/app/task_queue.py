import os

from celery_factory import celery_factory


task_queue = celery_factory()

if __name__ == '__main__':
    task_queue.start()
