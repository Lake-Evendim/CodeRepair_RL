"""Smoke tests to verify project scaffolding works."""

import minirepair


def test_package_imports():
    assert hasattr(minirepair, "__name__")


def test_subpackages_import():
    from minirepair import agents, data, env, evaluation, training

    assert env.__name__ == "minirepair.env"
    assert data.__name__ == "minirepair.data"
    assert agents.__name__ == "minirepair.agents"
    assert training.__name__ == "minirepair.training"
    assert evaluation.__name__ == "minirepair.evaluation"
