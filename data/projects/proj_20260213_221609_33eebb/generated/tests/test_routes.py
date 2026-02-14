import unittest
from fastapi.testclient import TestClient
from src.routes import app

client = TestClient(app)

class TestTodoListAPI(unittest.TestCase):

    def test_create_task(self):
        response = client.post("/tasks/", json={"title": "New Task", "description": "Test task creation"})
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.json())
        self.assertEqual(response.json()["title"], "New Task")

    def test_get_tasks(self):
        response = client.get("/tasks/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_edit_task(self):
        # First create a task to edit
        create_response = client.post("/tasks/", json={"title": "Task to Edit", "description": "Edit this task"})
        task_id = create_response.json()["id"]

        # Now, edit the task
        response = client.put(f"/tasks/{task_id}", json={"title": "Edited Task", "description": "Task has been edited"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Edited Task")

    def test_delete_task(self):
        # First create a task to delete
        create_response = client.post("/tasks/", json={"title": "Task to Delete", "description": "Delete this task"})
        task_id = create_response.json()["id"]

        # Now, delete the task
        response = client.delete(f"/tasks/{task_id}")
        self.assertEqual(response.status_code, 204)

        # Verify the task is deleted
        get_response = client.get(f"/tasks/{task_id}")
        self.assertEqual(get_response.status_code, 404)

    def test_prioritize_task(self):
        # First create a task to prioritize
        create_response = client.post("/tasks/", json={"title": "Task to Prioritize", "description": "Prioritize this task"})
        task_id = create_response.json()["id"]

        # Now, prioritize the task
        response = client.put(f"/tasks/{task_id}/prioritize", json={"priority": "high"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["priority"], "high")

    def test_complete_task(self):
        # First create a task to complete
        create_response = client.post("/tasks/", json={"title": "Task to Complete", "description": "Complete this task"})
        task_id = create_response.json()["id"]

        # Now, complete the task
        response = client.put(f"/tasks/{task_id}/complete")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["completed"])

if __name__ == "__main__":
    unittest.main()