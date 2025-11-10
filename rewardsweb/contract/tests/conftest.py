import pytest
from algokit_utils import AlgorandClient


@pytest.fixture(scope="session", autouse=True)
def ensure_localnet_running():
    """Fails test session early if localnet / algod is not running."""
    try:
        client = AlgorandClient.from_environment().client.algod
        client.status()  # will throw if daemon not reachable
    except Exception as e:
        raise RuntimeError(
            "\n❌ Localnet is not running.\n"
            "Start it with:\n\n"
            "   algokit localnet start\n"
        ) from e

    print("\n✅ Localnet detected and running!\n")
