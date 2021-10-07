#!/bin/bash

echo "Running autoflake..."
autoflake --remove-all-unused-imports --recursive --in-place app --exclude=__init__.py,migrations
echo "\n"

echo "Running black"
black app
echo "\n"

echo "Running isort"
isort app
