"""
Tests for TaskManager service.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.task_manager import TaskManager, TaskStatus


class TestTaskManager:
    """Test cases for TaskManager."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = MagicMock()
        mock.exists.return_value = True
        mock.hgetall.return_value = {
            "task_id": "test-task-id",
            "type": "peer_comparison",
            "status": "pending",
            "progress": "0",
            "enterprise_id": "1",
            "user_id": "1",
            "error_message": "",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "metadata": "{}",
        }
        return mock

    @pytest.fixture
    def task_manager(self, mock_redis):
        """Create a TaskManager with mocked Redis."""
        tm = TaskManager()
        tm._client = mock_redis
        return tm

    def test_create_task(self, task_manager, mock_redis):
        """Test creating a new task."""
        mock_redis.hset.return_value = 1

        task_id = task_manager.create_task(
            task_type="peer_comparison",
            enterprise_id=1,
            user_id=1,
        )

        assert task_id is not None
        assert len(task_id) == 36  # UUID format
        mock_redis.hset.assert_called_once()

    def test_create_task_with_metadata(self, task_manager, mock_redis):
        """Test creating a task with metadata."""
        mock_redis.hset.return_value = 1

        task_id = task_manager.create_task(
            task_type="batch_import",
            metadata={"batch_size": 100, "years": 5},
        )

        assert task_id is not None
        # Check that hset was called with metadata
        call_args = mock_redis.hset.call_args
        mapping = call_args[1]["mapping"]
        assert "metadata" in mapping

    def test_update_task_status(self, task_manager, mock_redis):
        """Test updating task status."""
        mock_redis.exists.return_value = True
        mock_redis.hset.return_value = 1

        result = task_manager.update_task_status(
            task_id="test-task-id",
            status="running",
            progress=50,
        )

        assert result is True
        mock_redis.hset.assert_called_once()

    def test_update_task_status_nonexistent(self, task_manager, mock_redis):
        """Test updating a non-existent task."""
        mock_redis.exists.return_value = False

        result = task_manager.update_task_status(
            task_id="nonexistent-id",
            status="running",
        )

        assert result is False

    def test_update_task_with_error(self, task_manager, mock_redis):
        """Test updating task with error message."""
        mock_redis.exists.return_value = True
        mock_redis.hset.return_value = 1

        result = task_manager.update_task_status(
            task_id="test-task-id",
            status="failed",
            error_message="Connection timeout",
        )

        assert result is True

    def test_get_task_status(self, task_manager, mock_redis):
        """Test getting task status."""
        mock_redis.exists.return_value = True

        status = task_manager.get_task_status("test-task-id")

        assert status is not None
        assert status["task_id"] == "test-task-id"
        assert status["type"] == "peer_comparison"
        assert status["status"] == "pending"
        assert status["progress"] == 0
        assert status["enterprise_id"] == 1

    def test_get_task_status_nonexistent(self, task_manager, mock_redis):
        """Test getting status for non-existent task."""
        mock_redis.exists.return_value = False

        status = task_manager.get_task_status("nonexistent-id")

        assert status is None

    def test_list_tasks(self, task_manager, mock_redis):
        """Test listing tasks."""
        mock_redis.scan_iter.return_value = ["task:task-1", "task:task-2"]
        mock_redis.hgetall.side_effect = [
            {
                "task_id": "task-1",
                "type": "peer_comparison",
                "status": "completed",
                "progress": "100",
                "enterprise_id": "1",
                "user_id": "1",
                "error_message": "",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:01:00",
                "metadata": "{}",
            },
            {
                "task_id": "task-2",
                "type": "batch_import",
                "status": "running",
                "progress": "50",
                "enterprise_id": "",
                "user_id": "2",
                "error_message": "",
                "created_at": "2024-01-02T00:00:00",
                "updated_at": "2024-01-02T00:00:30",
                "metadata": "{}",
            },
        ]

        tasks = task_manager.list_tasks()

        assert len(tasks) == 2
        assert tasks[0]["task_id"] == "task-2"  # Sorted by created_at desc

    def test_list_tasks_with_filter(self, task_manager, mock_redis):
        """Test listing tasks with status filter."""
        mock_redis.scan_iter.return_value = ["task:task-1", "task:task-2"]
        mock_redis.hgetall.side_effect = [
            {
                "task_id": "task-1",
                "type": "peer_comparison",
                "status": "completed",
                "progress": "100",
                "enterprise_id": "1",
                "user_id": "1",
                "error_message": "",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:01:00",
                "metadata": "{}",
            },
            {
                "task_id": "task-2",
                "type": "batch_import",
                "status": "running",
                "progress": "50",
                "enterprise_id": "",
                "user_id": "2",
                "error_message": "",
                "created_at": "2024-01-02T00:00:00",
                "updated_at": "2024-01-02T00:00:30",
                "metadata": "{}",
            },
        ]

        tasks = task_manager.list_tasks(status="running")

        assert len(tasks) == 1
        assert tasks[0]["status"] == "running"

    def test_delete_task(self, task_manager, mock_redis):
        """Test deleting a task."""
        mock_redis.delete.return_value = 1

        result = task_manager.delete_task("test-task-id")

        assert result is True
        mock_redis.delete.assert_called_once()

    def test_delete_task_nonexistent(self, task_manager, mock_redis):
        """Test deleting a non-existent task."""
        mock_redis.delete.return_value = 0

        result = task_manager.delete_task("nonexistent-id")

        assert result is False

    def test_set_task_expiry(self, task_manager, mock_redis):
        """Test setting task expiry."""
        mock_redis.expire.return_value = True

        result = task_manager.set_task_expiry("test-task-id", 3600)

        assert result is True
        mock_redis.expire.assert_called_once()

    def test_progress_clamping(self, task_manager, mock_redis):
        """Test progress is clamped to 0-100 range."""
        mock_redis.exists.return_value = True
        mock_redis.hset.return_value = 1

        # Test upper bound
        task_manager.update_task_status("test-task-id", progress=150)
        call_args = mock_redis.hset.call_args
        mapping = call_args[1]["mapping"]
        assert mapping["progress"] == "100"

        # Test lower bound
        task_manager.update_task_status("test-task-id", progress=-10)
        call_args = mock_redis.hset.call_args
        mapping = call_args[1]["mapping"]
        assert mapping["progress"] == "0"


class TestTaskStatus:
    """Test cases for TaskStatus enum."""

    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"

    def test_task_status_is_string(self):
        """Test TaskStatus can be used as string."""
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.RUNNING == "running"  # Direct equality works
