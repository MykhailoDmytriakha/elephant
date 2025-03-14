# Testing the Backend API

This directory contains tests for the backend API. The tests use pytest and FastAPI's TestClient to test the API endpoints.

## Running Tests

To run all tests:

```bash
cd backend
pytest -v
```

To run a specific test file:

```bash
cd backend
pytest -v tests/test_user_queries_routes.py
```

To run a specific test:

```bash
cd backend
pytest -v tests/test_user_queries_routes.py::TestUserQueriesRoutes::test_create_user_query
```

## Test Coverage

To run tests with coverage:

```bash
cd backend
pytest --cov=src tests/
```

For a detailed coverage report:

```bash
cd backend
pytest --cov=src --cov-report=html tests/
```

This will generate a directory called `htmlcov/` where you can open `index.html` to see the coverage report.

## Test Structure

The tests use fixtures to mock the database service, allowing for testing without an actual database connection. This makes the tests faster and more reliable.

### Key components of tests:

1. **Fixtures**: Used to set up mock objects and data for tests
2. **Patching**: Used to replace dependencies with mock objects
3. **TestClient**: Used to make HTTP requests to the API
4. **Assertions**: Used to verify the response status code and content

## Adding New Tests

When adding new tests:

1. Create a new test file named `test_<module_name>.py`
2. Use the existing patterns for mocking dependencies
3. Make sure to test both the success and failure paths
4. Verify that all edge cases are covered 