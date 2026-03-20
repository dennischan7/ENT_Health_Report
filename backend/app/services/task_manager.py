"""
Redis-based task status management service.

This module provides functionality to track task status in Redis for
long-running operations like batch imports, report generation, etc.
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

import redis
from redis.exceptions import RedisError

from app.core.config import settings


class TaskStatus(str, Enum):
    """Task status enum."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskManager:
    """
    Service for managing task status in Redis.

    This service handles:
    - Creating new tasks
    - Updating task status and progress
    - Retrieving task status
    - Listing tasks by user

    Attributes:
        redis_client: Redis client instance.
        key_prefix: Prefix for all task keys.

    Example:
        >>> from app.services.task_manager import TaskManager
        >>> task_mgr = TaskManager()
        >>> task_id = task_mgr.create_task("peer_comparison", enterprise_id=1)
        >>> task_mgr.update_task_status(task_id, "running", progress=50)
        >>> status = task_mgr.get_task_status(task_id)
        >>> assert status["status"] == "running"
        >>> assert status["progress"] == 50
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize the TaskManager with Redis connection.

        Args:
            redis_url: Optional Redis URL. Defaults to settings.REDIS_URL.
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self.key_prefix = "task:"
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> redis.Redis:
        """Get or create Redis client (lazy initialization)."""
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    def _generate_task_id(self) -> str:
        """Generate a unique task ID."""
        return str(uuid.uuid4())

    def _task_key(self, task_id: str) -> str:
        """Get Redis key for a task."""
        return f"{self.key_prefix}{task_id}"

    def create_task(
        self,
        task_type: str,
        enterprise_id: Optional[int] = None,
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new task and return its ID.

        Args:
            task_type: Type of task (e.g., "peer_comparison", "batch_import").
            enterprise_id: Optional enterprise ID associated with the task.
            user_id: Optional user ID who created the task.
            metadata: Optional additional metadata for the task.

        Returns:
            The generated task ID.
        """
        task_id = self._generate_task_id()
        now = datetime.utcnow().isoformat()

        task_data = {
            "task_id": task_id,
            "type": task_type,
            "status": TaskStatus.PENDING.value,
            "progress": 0,
            "enterprise_id": enterprise_id,
            "user_id": user_id,
            "error_message": None,
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {},
        }

        key = self._task_key(task_id)
        self.client.hset(
            key,
            mapping={
                k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) if v is not None else ""
                for k, v in task_data.items()
            },
        )

        return task_id

    def update_task_status(
        self,
        task_id: str,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update task status, progress, or error message.

        Args:
            task_id: The task ID to update.
            status: New status (pending, running, completed, failed).
            progress: Progress percentage (0-100).
            error_message: Error message if task failed.
            metadata: Additional metadata to merge.

        Returns:
            True if update was successful, False otherwise.
        """
        key = self._task_key(task_id)

        # Check if task exists
        if not self.client.exists(key):
            return False

        updates = {"updated_at": datetime.utcnow().isoformat()}

        if status is not None:
            updates["status"] = status

        if progress is not None:
            updates["progress"] = str(max(0, min(100, progress)))

        if error_message is not None:
            updates["error_message"] = error_message

        if metadata is not None:
            # Merge with existing metadata
            existing_metadata = self.client.hget(key, "metadata")
            if existing_metadata:
                try:
                    merged = json.loads(existing_metadata)
                    merged.update(metadata)
                    updates["metadata"] = json.dumps(merged)
                except json.JSONDecodeError:
                    updates["metadata"] = json.dumps(metadata)
            else:
                updates["metadata"] = json.dumps(metadata)

        self.client.hset(key, mapping=updates)
        return True

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task status by task ID.

        Args:
            task_id: The task ID to query.

        Returns:
            Dictionary with task data or None if not found.
        """
        key = self._task_key(task_id)

        if not self.client.exists(key):
            return None

        data = self.client.hgetall(key)

        # Parse values
        result = {}
        for k, v in data.items():
            if k == "progress":
                result[k] = int(v) if v else 0
            elif k == "enterprise_id" or k == "user_id":
                result[k] = int(v) if v else None
            elif k == "metadata":
                try:
                    result[k] = json.loads(v) if v else {}
                except json.JSONDecodeError:
                    result[k] = {}
            elif k == "error_message":
                result[k] = v if v else None
            else:
                result[k] = v

        return result

    def list_tasks(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List tasks with optional filters.

        Args:
            user_id: Filter by user ID.
            status: Filter by status.
            task_type: Filter by task type.
            limit: Maximum number of tasks to return.

        Returns:
            List of task dictionaries.
        """
        tasks = []
        pattern = f"{self.key_prefix}*"
        keys = list(self.client.scan_iter(match=pattern, count=limit + 100))[: limit + 100]

        for key in keys:
            data = self.client.hgetall(key)
            if not data:
                continue

            # Parse values
            task = {}
            for k, v in data.items():
                if k == "progress":
                    task[k] = int(v) if v else 0
                elif k == "enterprise_id" or k == "user_id":
                    task[k] = int(v) if v else None
                elif k == "metadata":
                    try:
                        task[k] = json.loads(v) if v else {}
                    except json.JSONDecodeError:
                        task[k] = {}
                elif k == "error_message":
                    task[k] = v if v else None
                else:
                    task[k] = v

            # Apply filters
            if user_id is not None and task.get("user_id") != user_id:
                continue
            if status is not None and task.get("status") != status:
                continue
            if task_type is not None and task.get("type") != task_type:
                continue

            tasks.append(task)

            if len(tasks) >= limit:
                break

        # Sort by created_at descending (newest first)
        tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return tasks[:limit]

    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task by ID.

        Args:
            task_id: The task ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        key = self._task_key(task_id)
        return bool(self.client.delete(key))

    def set_task_expiry(self, task_id: str, seconds: int) -> bool:
        """
        Set expiry time for a task.

        Args:
            task_id: The task ID.
            seconds: Time to live in seconds.

        Returns:
            True if successful, False otherwise.
        """
        key = self._task_key(task_id)
        return self.client.expire(key, seconds)

    def close(self):
        """Close the Redis connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
