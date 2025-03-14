#!/bin/bash

# Navigate to the project root directory
cd $(dirname $0)/../..

# Set the PYTHONPATH to include the backend directory
export PYTHONPATH=backend

# Run tests with coverage
coverage run -m pytest backend/tests

# Generate a coverage report
coverage report

# Optionally, generate an HTML report
coverage html 