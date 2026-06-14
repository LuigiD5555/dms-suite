# Test Suite

## Installation

```bash
pip install -r requirements.txt
```

## Running Tests

Run the complete suite:

```bash
pytest
```

Run one file:

```bash
pytest tests/test_auth.py
```

Show more detail:

```bash
pytest -vv
```

Run only the tests that failed last time:

```bash
pytest --lf
```

## Structure

```text
tests/
├── conftest.py                    Shared users and HTTP client fixtures
├── test_auth.py                   Authentication and access control
├── test_iframe_admin_targets.py   Public view to admin iframe contracts
├── test_import_cp.py              ZIP-code import commands
├── test_models.py                 Main model behavior
├── test_urls.py                   URL resolution and responses
└── test_views_data.py             Data views and autocomplete endpoints
```

## Coverage

`test_auth.py`

- Login and logout behavior
- Authentication redirects
- Staff, superuser, and Superboss access
- Registration permissions

`test_urls.py`

- Named URL registration
- Critical route responses
- Admin proxy URL compatibility

`test_models.py`

- User creation, full names, and password hashing
- ZIP-code normalization and database routing
- Organization and person behavior
- Profile defaults

`test_import_cp.py`

- Clean CSV import
- Duplicate prevention
- Existing-record updates
- Missing-file handling
- Resumable imports

`test_views_data.py`

- Data view responses
- Authenticated requests
- Autocomplete endpoints

`test_iframe_admin_targets.py`

- Rendered iframe targets
- Admin URL availability
- Proxy model-name contracts
