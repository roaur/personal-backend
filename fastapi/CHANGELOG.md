# Changelog

## [0.2.1](https://github.com/roaur/personal-backend/compare/fastapi-service-v0.2.0...fastapi-service-v0.2.1) (2025-11-27)


### Bug Fixes

* do not accidentially skip new opponent matches ([2cd484b](https://github.com/roaur/personal-backend/commit/2cd484b1c140edb81d7839303a92b01abf0f9303))

## [0.2.0](https://github.com/roaur/personal-backend/compare/fastapi-service-v0.1.0...fastapi-service-v0.2.0) (2025-11-27)


### Features

* Add player depth and last fetch time, and implement concurrent opponent processing via Celery and FastAPI. ([a398192](https://github.com/roaur/personal-backend/commit/a3981925111f019ce0395d082d90b51c24754106))
* Implement batch processing for games and players, remove devcontainer and Traefik configurations, and add documentation and tests. ([c842352](https://github.com/roaur/personal-backend/commit/c8423528279ac4d30c43df74a483bef551943e42))
* Implement Lichess API pagination and resumable game fetching using `last_move_time` as the cursor. ([9225b71](https://github.com/roaur/personal-backend/commit/9225b7152dddb5ed049fbd58d39f394c37763ace))
* Introduce player-specific last move time API, refactor Celery tasks for generic player updates with idempotency, and reduce player update frequency to 1 hour. ([5a7d0e6](https://github.com/roaur/personal-backend/commit/5a7d0e6366fa0b9df627aa4499373d15bdbbfb45))
* jsonb column for game metrics ([403c6d7](https://github.com/roaur/personal-backend/commit/403c6d7b7dfe39d0c23c5746d7511cad8a63d391))
* migrate Lichess match pulling from Airflow to Celery, adding new Celery service files and removing Airflow components. ([57d530a](https://github.com/roaur/personal-backend/commit/57d530a30cc302e47b2a6e744beb3036b1e97ab3))
