import os
import shutil
import tempfile

import pytest
from fastapi.testclient import TestClient

_TEST_DIR = tempfile.mkdtemp(prefix="menu-maker-tests-")
_TEST_DB = os.path.join(_TEST_DIR, "test_menu_maker.db")

os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["PUBLIC_BASE_URL"] = "https://example.test"
os.environ["MENU_MAKER_SECRET"] = "test-secret"

from main import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(_TEST_DIR, ignore_errors=True)
