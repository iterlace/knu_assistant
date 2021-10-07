#!/bin/bash

echo "Running autoflake..."
autoflake --remove-all-unused-imports --recursive --in-place assistant --exclude=__init__.py,migrations
echo "\n"

echo "Running black"
black assistant
echo "\n"

echo "Running isort"
isort assistant
