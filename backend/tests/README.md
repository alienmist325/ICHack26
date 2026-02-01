# Backend Testing Guide

This directory contains comprehensive unit, integration, and end-to-end tests for the Rightmove Property Rental Finder API.

## Overview

The test suite covers:
- **Authentication** - User registration, login, JWT tokens, password hashing
- **User Management** - Profiles, preferences, notifications
- **Property Interactions** - Starring, status tracking, comments
- **Shared Feeds** - Collaborative wishlists, members, property sharing
- **Viewing Calendar** - Event scheduling, iCalendar export
- **End-to-End Flows** - Complete user journeys

## Quick Start

### Running All Tests

```bash
# Install dependencies (if not already done)
pip install pytest pytest-cov

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=html
```

### Running Specific Test Categories

```bash
# Authentication tests only
pytest -m auth

# Database/CRUD tests only
pytest -m db

# Integration tests only
pytest -m integration

# Unit tests only
pytest -m unit
```

### Running Individual Test Files

```bash
# Test authentication
pytest tests/test_auth.py

# Test properties
pytest tests/test_properties.py

# Test user profiles
pytest tests/test_users.py

# Test shared feeds
pytest tests/test_shared_feeds.py

# Test viewing calendar
pytest tests/test_viewings.py

# Test user journeys
pytest tests/test_user_journeys.py
```

### Running Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/test_auth.py::TestPasswordHashing

# Run a specific test function
pytest tests/test_auth.py::TestPasswordHashing::test_hash_password_creates_different_hash
```

## Test Structure

### `conftest.py`

Pytest configuration and shared fixtures:

- `client` - FastAPI TestClient for making HTTP requests
- `test_user` - Creates a test user in the database
- `test_user_tokens` - Generates JWT tokens for a test user
- `authenticated_client` - TestClient with auth headers pre-configured
- `test_user_data` - Standard test user data
- `second_test_user` - Creates a second test user (for multi-user scenarios)
- `mock_property_data` - Sample property data for tests
- `mock_property_data_rental` - Sample rental property data

Features:
- Automatic test database setup/teardown
- Database clearing between tests for isolation
- Custom markers for test categorization

### Test Files

#### `test_auth.py`

Tests for authentication functionality:

- **TestPasswordHashing** - Password hashing and verification
  - `test_hash_password_creates_different_hash`
  - `test_verify_password_correct`
  - `test_verify_password_incorrect`
  - `test_same_password_produces_different_hashes`

- **TestJWTTokens** - JWT token creation and verification
  - `test_create_access_token`
  - `test_verify_token_valid`
  - `test_verify_token_invalid`

- **TestUserRegistration** - User registration flow
  - `test_create_user_successfully`
  - `test_create_duplicate_user_fails`
  - `test_get_user_by_email`

- **TestAuthenticationEndpoints** - API endpoint tests
  - `test_register_endpoint`
  - `test_login_endpoint`
  - `test_refresh_token_endpoint`
  - `test_get_current_user`

#### `test_properties.py`

Tests for property interactions:

- **TestPropertyStarring** - Bookmark/star functionality
  - `test_star_property`
  - `test_unstar_property`
  - `test_get_user_stars_multiple`
  - `test_star_pagination`

- **TestPropertyStatus** - Status tracking (interested → viewing → offer → accepted)
  - `test_set_property_status_interested`
  - `test_update_property_status`
  - `test_status_independent_per_user`

- **TestPropertyComments** - Property comment management
  - `test_add_comment`
  - `test_get_property_comments`
  - `test_delete_comment`

- **TestPropertyEndpoints** - API endpoints for properties
  - `test_star_property_endpoint`
  - `test_add_comment_endpoint`
  - `test_delete_comment_endpoint`

#### `test_users.py`

Tests for user profiles and preferences:

- **TestUserProfile** - Profile management
  - `test_create_user_profile`
  - `test_update_user_profile`
  - `test_profile_with_locations`
  - `test_profile_price_range`

- **TestUserProfileEndpoints** - Profile API endpoints
  - `test_get_profile_endpoint`
  - `test_update_profile_endpoint`
  - `test_delete_account_endpoint`

- **TestNotificationSettings** - Notification preferences
  - `test_update_notification_settings`
  - `test_get_notification_settings`

#### `test_shared_feeds.py`

Tests for collaborative wishlists:

- **TestSharedFeedsCreation** - Feed creation and management
  - `test_create_shared_feed`
  - `test_get_shared_feed`
  - `test_shared_feed_has_unique_invite_code`

- **TestSharedFeedMembers** - Member management
  - `test_add_member_to_feed`
  - `test_remove_member_from_feed`
  - `test_max_members_limit`

- **TestSharedFeedProperties** - Managing properties in feeds
  - `test_add_property_to_feed`
  - `test_get_shared_feed_properties`

- **TestSharedFeedsEndpoints** - API endpoints
  - `test_create_feed_endpoint`
  - `test_add_member_endpoint`
  - `test_add_property_to_feed_endpoint`

#### `test_viewings.py`

Tests for viewing calendar:

- **TestViewingCreation** - Event management
  - `test_create_viewing_event`
  - `test_update_viewing_event`
  - `test_get_upcoming_viewings`

- **TestViewingEndpoints** - API endpoints
  - `test_create_viewing_endpoint`
  - `test_get_viewings_endpoint`

- **TestICalendarExport** - iCalendar export
  - `test_export_single_viewing_as_ical`
  - `test_export_all_viewings_as_ical`
  - `test_ical_export_valid_format`

#### `test_user_journeys.py`

Complete end-to-end user workflows:

- **TestCompleteAuthenticationFlow**
  - `test_user_registration_login_logout_flow`
  - `test_user_registration_with_profile_setup`

- **TestPropertyDiscoveryFlow**
  - `test_search_star_comment_property_flow`
  - `test_property_status_progression`
  - `test_bookmark_multiple_properties_flow`

- **TestViewingCalendarFlow**
  - `test_schedule_viewing_and_export_flow`
  - `test_schedule_multiple_viewings_flow`

- **TestSharedFeedCollaborationFlow**
  - `test_create_feed_invite_add_properties_flow`
  - `test_multiple_users_collaborating_flow`

- **TestErrorHandlingFlow**
  - `test_invalid_credentials_flow`
  - `test_access_protected_resource_without_auth`

## Test Markers

Tests are marked with decorators for easy categorization:

```python
@pytest.mark.unit          # Unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.auth          # Authentication-related
@pytest.mark.db            # Database/CRUD operations
```

## Fixtures

### Authentication Fixtures

```python
def test_something(test_user):
    """Access the test user"""
    assert test_user["email"] == "testuser@example.com"

def test_authenticated(authenticated_client):
    """Use a pre-authenticated client"""
    response = authenticated_client.get("/users/profile")
    assert response.status_code == 200
```

### Multi-User Fixtures

```python
def test_multi_user(test_user, second_test_user, second_user_tokens):
    """Work with multiple users"""
    # test_user and second_test_user are different
    assert test_user["id"] != second_test_user["id"]
```

### Property Fixtures

```python
def test_property(mock_property_data):
    """Use sample property data"""
    from app.crud import create_property
    prop = create_property(mock_property_data)
    assert prop["price"] == 450000
```

## Running Tests in CI/CD

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt pytest pytest-cov
      - run: pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Coverage

Generate coverage reports:

```bash
# Terminal report
pytest --cov=app

# HTML report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser

# XML report (for CI/CD)
pytest --cov=app --cov-report=xml
```

## Writing New Tests

### Basic Unit Test

```python
@pytest.mark.unit
def test_something(test_user):
    """Test a specific function."""
    from app.crud import some_function
    result = some_function(test_user["id"])
    assert result is not None
```

### Integration Test

```python
@pytest.mark.integration
def test_api_endpoint(authenticated_client):
    """Test an API endpoint."""
    response = authenticated_client.get("/users/profile")
    assert response.status_code == 200
    assert response.json()["email"]
```

### Multi-User Test

```python
@pytest.mark.integration
def test_collaboration(authenticated_client, second_user_tokens):
    """Test interaction between users."""
    # authenticated_client is user 1
    response1 = authenticated_client.post("/shared-feeds", json={"name": "Feed"})
    
    # Switch to user 2
    authenticated_client.headers = {"Authorization": f"Bearer {second_user_tokens['access_token']}"}
    response2 = authenticated_client.get("/shared-feeds")
    
    assert response2.status_code == 200
```

## Debugging Tests

### Verbose Output

```bash
pytest -v --tb=short tests/test_auth.py::TestAuthenticationEndpoints::test_login_endpoint
```

### Print Debugging

```python
def test_something(test_user):
    print(f"User: {test_user}")  # Will print when test fails
    assert True
```

### PDB Debugger

```bash
pytest --pdb  # Drops into debugger on failure
```

### Capture Output

```bash
pytest -s  # Show print statements
```

## Common Issues

### "create_user is unknown import symbol"

Make sure `app.crud.create_user` exists and is properly exported.

### "PRAGMA foreign_keys = ON" errors

These are database schema issues. Ensure all tables exist and foreign keys are properly configured.

### Test isolation issues

If tests are failing because of state from previous tests:
1. Check that `clear_database` fixture is being used
2. Ensure each test creates its own data
3. Don't rely on test execution order

## Contributing

When adding new features:

1. Write tests for the new functionality
2. Place tests in appropriate file
3. Use consistent naming: `test_<action>_<scenario>`
4. Add docstrings explaining what's being tested
5. Run full test suite: `pytest`
6. Aim for 80%+ code coverage

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
