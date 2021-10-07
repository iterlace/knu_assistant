#!/bin/bash

echo "\nRunning black..."
black assistant --check

echo "\nRunning flake8..."
flake8 assistant

echo "\nRunning pylint..."
pylint assistant --disable=all --enable C0411 # import order, feel free to add new checks
