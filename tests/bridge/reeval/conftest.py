from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

from app.integrations import MockAuditLogger
from app.integrations import MockDataBridge


@pytest_asyncio.fixture
async def data_bridge() -> AsyncIterator[MockDataBridge]:
    bridge = MockDataBridge()
    await bridge.connect()
    yield bridge
    await bridge.disconnect()


@pytest.fixture
def audit_logger() -> MockAuditLogger:
    return MockAuditLogger()
