install:
	@pipenv install --dev

run:
	@FLASK_APP=app.py pipenv run flask run

lint:
	@pipenv run flake8

.PHONY: install run lint

