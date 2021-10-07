#!/bin/bash

echo "\nRunning black..."
black app --check

echo "\nRunning flake8..."
flake8 app

echo "\nRunning pylint..."
pylint app --disable=all --enable C0411 # import order, feel free to add new checks
