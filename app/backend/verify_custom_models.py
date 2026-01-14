import asyncio
import os
import sys

import httpx

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "src"))

from research_agent.api.auth.supabase import UserContext, get_current_user, get_optional_user
from research_agent.main import app


# Mock auth
def mock_get_current_user():
    return "test-user-id"


def mock_get_optional_user():
    return UserContext(user_id="test-user-id", is_anonymous=False)


app.dependency_overrides[get_current_user] = mock_get_current_user
app.dependency_overrides[get_optional_user] = mock_get_optional_user


async def test_custom_models():
    print("Testing Custom Models API (Async)...")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 0. Cleanup (idempotency)
        try:
            # We need to find the ID first to delete
            resp = await client.get("/api/v1/settings/custom-models")
            if resp.status_code == 200:
                for m in resp.json():
                    if m["model_id"] == "openai/gpt-4o-custom-async":
                        print(f"Cleaning up existing test model: {m['id']}")
                        await client.delete(f"/api/v1/settings/custom-models/{m['id']}")
        except Exception as e:
            print(f"Cleanup warning: {e}")

        # 1. List
        resp = await client.get("/api/v1/settings/custom-models")
        assert resp.status_code == 200, f"List failed: {resp.text}"
        initial_models = resp.json()
        print(f"Initial list models: {len(initial_models)}")

        # 2. Create
        model_data = {
            "model_id": "openai/gpt-4o-custom-async",
            "label": "GPT-4o Custom Async",
            "description": "Async verification test",
            "provider": "openai",
            "context_window": 128000,
        }

        resp = await client.post("/api/v1/settings/custom-models", json=model_data)
        if resp.status_code != 201:
            print(f"Create failed: {resp.text}")
            return

        created_model = resp.json()
        print(f"Created model: {created_model['id']}")
        assert created_model["model_id"] == model_data["model_id"]

        # 3. List (should increase)
        resp = await client.get("/api/v1/settings/custom-models")
        models = resp.json()
        # Verify count increased by 1
        assert len(models) == len(initial_models) + 1
        print(f"List models after create: {len(models)}")

        # 4. Update
        model_id = created_model["id"]
        update_data = {"label": "GPT-4o Custom Async Updated"}
        resp = await client.put(f"/api/v1/settings/custom-models/{model_id}", json=update_data)
        assert resp.status_code == 200, f"Update failed: {resp.text}"
        updated_model = resp.json()
        assert updated_model["label"] == "GPT-4o Custom Async Updated"
        print("Updated model")

        # 5. Get Metadata (should include custom model)
        resp = await client.get("/api/v1/settings/metadata")
        assert resp.status_code == 200, f"Metadata failed: {resp.text}"
        metadata = resp.json()["settings"]
        llm_options = metadata["llm_model"]["options"]
        found = False
        for opt in llm_options:
            if opt["value"] == "openai/gpt-4o-custom-async":
                found = True
                print(f"Found custom model in metadata: {opt}")
                break
        assert found, "Custom model not found in metadata options"

        # 6. Delete
        resp = await client.delete(f"/api/v1/settings/custom-models/{model_id}")
        assert resp.status_code == 204, f"Delete failed: {resp.text}"
        print("Deleted model")

        # 7. List (should decrease)
        resp = await client.get("/api/v1/settings/custom-models")
        models_after = resp.json()
        assert len(models_after) == len(initial_models)
        print("Verification Passed!")


if __name__ == "__main__":
    asyncio.run(test_custom_models())
