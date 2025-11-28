# Changelog

## [0.3.1](https://github.com/roaur/personal-backend/compare/celery-service-v0.3.0...celery-service-v0.3.1) (2025-11-28)


### Bug Fixes

* **celery:** deduplicate analysis ([9f9f194](https://github.com/roaur/personal-backend/commit/9f9f194c4d662c1fa212289827890dfefc9e132d))
* **celery:** test deduplication ([3ece513](https://github.com/roaur/personal-backend/commit/3ece5138053f9ba6af3f5b9e2a17cc10b1f027e3))

## [0.3.0](https://github.com/roaur/personal-backend/compare/celery-service-v0.2.1...celery-service-v0.3.0) (2025-11-28)


### Features

* add analysis workers to compose ([b612593](https://github.com/roaur/personal-backend/commit/b612593a833b397e0425c79ca29331f72a5c26a8))
* **celery:** implement background chess analysis engine ([b523b10](https://github.com/roaur/personal-backend/commit/b523b109cad843ad4f78d2c8086e6a30366228fb))


### Bug Fixes

* **celery:** handle forced mates and update from centipawns to eval ([24d056e](https://github.com/roaur/personal-backend/commit/24d056edc268ea401d06e9737ab6fd9361045263))
* fix path for stockfish in consumer ([7079d29](https://github.com/roaur/personal-backend/commit/7079d29fb5f081643f30536c33a4fd0f82f1398d))

## [0.2.1](https://github.com/roaur/personal-backend/compare/celery-service-v0.2.0...celery-service-v0.2.1) (2025-11-27)


### Bug Fixes

* do not continuously retry if player fetch is 404 ([63b6d04](https://github.com/roaur/personal-backend/commit/63b6d04d73322d67d5d2e026e2a395b17e25b715))

## [0.2.0](https://github.com/roaur/personal-backend/compare/celery-service-v0.1.0...celery-service-v0.2.0) (2025-11-27)


### Features

* Add player depth and last fetch time, and implement concurrent opponent processing via Celery and FastAPI. ([a398192](https://github.com/roaur/personal-backend/commit/a3981925111f019ce0395d082d90b51c24754106))
* Implement batch processing for games and players, remove devcontainer and Traefik configurations, and add documentation and tests. ([c842352](https://github.com/roaur/personal-backend/commit/c8423528279ac4d30c43df74a483bef551943e42))
* Implement Lichess API pagination and resumable game fetching using `last_move_time` as the cursor. ([9225b71](https://github.com/roaur/personal-backend/commit/9225b7152dddb5ed049fbd58d39f394c37763ace))
* Introduce player-specific last move time API, refactor Celery tasks for generic player updates with idempotency, and reduce player update frequency to 1 hour. ([5a7d0e6](https://github.com/roaur/personal-backend/commit/5a7d0e6366fa0b9df627aa4499373d15bdbbfb45))
* migrate Lichess match pulling from Airflow to Celery, adding new Celery service files and removing Airflow components. ([57d530a](https://github.com/roaur/personal-backend/commit/57d530a30cc302e47b2a6e744beb3036b1e97ab3))
