"""Integration tests for canvas operations."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_initial_canvas(client: AsyncClient):
    """Test that a canvas is automatically created with a project or can be retrieved."""
    # Create project
    create_res = await client.post(
        "/api/v1/projects",
        json={"name": "Canvas Test Project"}
    )
    project_id = create_res.json()["id"]

    # Get Canvas
    response = await client.get(f"/api/v1/projects/{project_id}/canvas")

    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data


@pytest.mark.asyncio
async def test_update_canvas(client: AsyncClient, sample_canvas_data):
    """Test updating the canvas."""
    # Create project
    create_res = await client.post(
        "/api/v1/projects",
        json={"name": "Update Canvas Project"}
    )
    project_id = create_res.json()["id"]

    # Update Canvas
    response = await client.put(
        f"/api/v1/projects/{project_id}/canvas",
        json=sample_canvas_data
    )

    assert response.status_code == 200

    # Verify update
    get_res = await client.get(f"/api/v1/projects/{project_id}/canvas")
    assert get_res.status_code == 200
    saved_data = get_res.json()

    # Check if 'nodes' is in the root
    assert "nodes" in saved_data
    assert len(saved_data["nodes"]) == 1
    assert saved_data["nodes"][0]["title"] == "Test Card"
