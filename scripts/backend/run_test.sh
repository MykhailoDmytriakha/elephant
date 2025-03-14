#!/bin/bash

# Navigate to the project root directory
cd $(dirname $0)/../..

# Set environment variables directly (will be overridden by conftest.py)
export OPENAI_API_KEY="dummy-key-for-testing"

# Set the PYTHONPATH to include the backend directory
export PYTHONPATH=backend

# Default to running all tests if no arguments provided
TEST_TARGET=${1:-backend/tests/test_user_queries_routes.py}

echo "Running tests for: $TEST_TARGET"

# Run tests with coverage
coverage run -m pytest $TEST_TARGET -v

# For more detailed analysis
echo ""
echo "Full coverage report for all modules:"
coverage report -m

# Generate an HTML report
coverage html 

echo ""
echo "HTML coverage report generated in htmlcov/index.html"
echo "Open this file in a browser to see detailed coverage information" 