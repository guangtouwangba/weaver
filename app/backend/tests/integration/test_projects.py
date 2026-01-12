"""Integration tests for project operations."""

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, db_session: AsyncSession):
    """Test creating a new project."""
    response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Integration Test Project",
            "description": "Created via integration test"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Integration Test Project"
    assert "id" in data

    # Verify in DB
    result = await db_session.execute(
        text(f"SELECT name FROM projects WHERE id = '{data['id']}'")
    )
    row = result.first()
    assert row is not None
    assert row[0] == "Integration Test Project"


@pytest.mark.asyncio
async def test_get_projects_list(client: AsyncClient):
    """Test listing projects."""
    # Create two projects
    await client.post("/api/v1/projects", json={"name": "Project A"})
    await client.post("/api/v1/projects", json={"name": "Project B"})

    response = await client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()

    # We expect at least 2 projects (there might be more from other tests if DB wasn't cleared,
    # but our fixture uses transaction rollback, so it should be clean per function)
    assert len(data["items"]) >= 2
    names = [p["name"] for p in data["items"]]
    assert "Project A" in names
    assert "Project B" in names


@pytest.mark.asyncio
async def test_get_project_by_id(client: AsyncClient):
    """Test retrieving a single project."""
    # Create
    create_res = await client.post(
        "/api/v1/projects",
        json={"name": "Single Project", "description": "Desc"}
    )
    project_id = create_res.json()["id"]

    # Get
    response = await client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == "Single Project"


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient, db_session: AsyncSession):
    """Test deleting a project."""
    # Create
    create_res = await client.post(
        "/api/v1/projects",
        json={"name": "To Delete"}
    )
    project_id = create_res.json()["id"]

    # Delete
    response = await client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204

    # Verify Gone via API
    get_res = await client.get(f"/api/v1/projects/{project_id}")
    assert get_res.status_code == 404

    # Verify Gone via DB
    result = await db_session.execute(
        text(f"SELECT * FROM projects WHERE id = '{project_id}'")
    )
    assert result.first() is None
