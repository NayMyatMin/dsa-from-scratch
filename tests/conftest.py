import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "property: randomized test against a brute-force oracle",
    )
    config.addinivalue_line(
        "markers",
        "slow: large input. A hang here means your solution is quadratic.",
    )
