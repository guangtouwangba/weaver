"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "description": "A test project for unit tests",
    }


@pytest.fixture
def sample_canvas_data():
    """Sample canvas data for testing."""
    return {
        "nodes": [
            {
                "id": "node-1",
                "type": "card",
                "title": "Test Card",
                "content": "Test content",
                "x": 100,
                "y": 200,
            }
        ],
        "edges": [],
        "viewport": {"x": 0, "y": 0, "scale": 1},
    }

