import pytest
from fastapi import status


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns correct response"""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "healthy"}

    def test_readiness_check(self, client):
        """Test readiness check endpoint"""
        response = client.get("/ready")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "ready"}


class TestTaskCreation:
    """Test task creation endpoints"""

    def test_create_task_success(self, client, sample_task):
        """Test creating a task successfully"""
        response = client.post("/api/tasks/", json=sample_task)
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["title"] == sample_task["title"]
        assert data["description"] == sample_task["description"]
        assert data["priority"] == sample_task["priority"]
        assert data["completed"] == False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_task_missing_title(self, client):
        """Test creating a task without title fails"""
        response = client.post("/api/tasks/", json={
            "description": "Test description",
            "priority": "high"
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_task_invalid_priority(self, client):
        """Test creating a task with invalid priority fails"""
        response = client.post("/api/tasks/", json={
            "title": "Test Task",
            "priority": "invalid"
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_task_with_high_priority(self, client):
        """Test creating a high priority task"""
        response = client.post("/api/tasks/", json={
            "title": "Urgent Task",
            "description": "This needs immediate attention",
            "priority": "high"
        })
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["priority"] == "high"


class TestTaskRetrieval:
    """Test task retrieval endpoints"""

    def test_get_empty_task_list(self, client):
        """Test getting tasks when none exist"""
        response = client.get("/api/tasks/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_task_list(self, client, sample_task):
        """Test getting list of tasks"""
        # Create a task first
        client.post("/api/tasks/", json=sample_task)

        response = client.get("/api/tasks/")
        assert response.status_code == status.HTTP_200_OK
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == sample_task["title"]

    def test_get_task_by_id(self, client, sample_task):
        """Test getting a specific task by ID"""
        # Create a task
        create_response = client.post("/api/tasks/", json=sample_task)
        task_id = create_response.json()["id"]

        # Get the task
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == sample_task["title"]

    def test_get_nonexistent_task(self, client):
        """Test getting a task that doesn't exist"""
        response = client.get("/api/tasks/9999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_filter_tasks_by_completion(self, client):
        """Test filtering tasks by completion status"""
        # Create completed and pending tasks
        client.post("/api/tasks/", json={"title": "Completed", "priority": "low"})
        create_response = client.post("/api/tasks/", json={"title": "Pending", "priority": "low"})

        # Mark first task as completed
        task_id = create_response.json()["id"]
        client.put(f"/api/tasks/{task_id}", json={"completed": True})

        # Get pending tasks
        response = client.get("/api/tasks/?completed=false")
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Pending"

    def test_filter_tasks_by_priority(self, client):
        """Test filtering tasks by priority"""
        # Create tasks with different priorities
        client.post("/api/tasks/", json={"title": "Low Priority", "priority": "low"})
        client.post("/api/tasks/", json={"title": "High Priority", "priority": "high"})

        # Get high priority tasks
        response = client.get("/api/tasks/?priority=high")
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["priority"] == "high"


class TestTaskUpdate:
    """Test task update endpoints"""

    def test_update_task_title(self, client, sample_task):
        """Test updating task title"""
        # Create a task
        create_response = client.post("/api/tasks/", json=sample_task)
        task_id = create_response.json()["id"]

        # Update the task
        response = client.put(f"/api/tasks/{task_id}", json={
            "title": "Updated Title"
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Title"

    def test_update_task_completion(self, client, sample_task):
        """Test marking task as completed"""
        # Create a task
        create_response = client.post("/api/tasks/", json=sample_task)
        task_id = create_response.json()["id"]

        # Mark as completed
        response = client.put(f"/api/tasks/{task_id}", json={
            "completed": True
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["completed"] == True

    def test_update_task_priority(self, client, sample_task):
        """Test updating task priority"""
        # Create a task
        create_response = client.post("/api/tasks/", json=sample_task)
        task_id = create_response.json()["id"]

        # Update priority
        response = client.put(f"/api/tasks/{task_id}", json={
            "priority": "high"
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["priority"] == "high"

    def test_update_nonexistent_task(self, client):
        """Test updating a task that doesn't exist"""
        response = client.put("/api/tasks/9999", json={
            "title": "Updated"
        })
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTaskDeletion:
    """Test task deletion endpoints"""

    def test_delete_task(self, client, sample_task):
        """Test deleting a task"""
        # Create a task
        create_response = client.post("/api/tasks/", json=sample_task)
        task_id = create_response.json()["id"]

        # Delete the task
        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify task is deleted
        get_response = client.get(f"/api/tasks/{task_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_task(self, client):
        """Test deleting a task that doesn't exist"""
        response = client.delete("/api/tasks/9999")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTaskStatistics:
    """Test task statistics endpoints"""

    def test_get_statistics_empty(self, client):
        """Test getting statistics when no tasks exist"""
        response = client.get("/api/tasks/stats/summary")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["completed"] == 0
        assert data["pending"] == 0

    def test_get_statistics_with_tasks(self, client):
        """Test getting statistics with tasks"""
        # Create tasks
        client.post("/api/tasks/", json={"title": "Task 1", "priority": "high"})
        create_response = client.post("/api/tasks/", json={"title": "Task 2", "priority": "low"})

        # Mark one as completed
        task_id = create_response.json()["id"]
        client.put(f"/api/tasks/{task_id}", json={"completed": True})

        # Get statistics
        response = client.get("/api/tasks/stats/summary")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2
        assert data["completed"] == 1
        assert data["pending"] == 1
        assert data["by_priority"]["high"] == 1
        assert data["by_priority"]["low"] == 1
