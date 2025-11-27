.PHONY: test test-celery

test: test-celery

test-celery:
	docker build -t celery-test ./celery
	docker run --rm celery-test pytest tests/
