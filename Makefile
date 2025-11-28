.PHONY: test test-celery

test: test-celery

test-celery:
	docker build -t celery-test ./celery
	docker run --rm -e PYTHONPATH=/app celery-test pytest tests/
