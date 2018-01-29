# Makefile

all: install

clean:
	@echo "Cleaning up"
	rm -rf build
	rm -rf dist
	find . -type f -regex ".*\.py[co]$$" -delete

test:
	venv/bin/python3 -m unittest tests/TestNoCoinCoin.py

install:
	python3 -m venv venv
	venv/bin/pip install -r requirements.txt
	venv/bin/pip install $(PWD)
#
