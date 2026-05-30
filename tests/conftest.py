import sys
from pathlib import Path
from typing import Iterator

ROOT: Path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.models import Database

@pytest.fixture
def client() -> Iterator[TestClient]:
    # 1. Create a fresh in-memory DB for this test
    test_db: Database = Database(":memory:")

    # 2. Define override that returns THIS db
    def override_get_db() -> Database:
        return test_db

    # 3. Apply override
    app.dependency_overrides[get_db] = override_get_db

    # 4. Create test client
    with TestClient(app) as client:
        yield client

    # 5. Cleanup (very important)
    app.dependency_overrides.clear()