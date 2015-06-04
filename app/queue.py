from celery import Celery


queue_app = Celery('app',
		broker='redis://redis',
		include=['app.ingest'])


if __name__ == '__main__':
    queue_app.start()
