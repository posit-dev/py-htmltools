#!/bin/sh
python setup.py sdist --format=zip
pip install dist/htmltools*.zip 