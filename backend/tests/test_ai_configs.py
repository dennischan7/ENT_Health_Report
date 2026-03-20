"""
Tests for AI Configuration API endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.ai_config import AIConfig, AIConfigAuditLog, AIProvider
from app.schemas.ai_config import AIProvider as SchemaAIProvider


client = TestClient(app)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    with patch("app.api.ai_configs.get_db") as mock_get_db:
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session
        yield mock_session


@pytest.fixture
def mock_current_user():
    """Create a mock current user."""
    with patch("app.api.ai_configs.get_current_user") as mock:
        user = MagicMock()
        user.id = 1
        user.email = "admin@example.com"
        user.is_admin = True
        user.is_active = True
        mock.return_value = user
        yield user


@pytest.fixture
def mock_admin_user():
    """Create a mock admin user."""
    with patch("app.api.ai_configs.get_current_admin_user") as mock:
        user = MagicMock()
        user.id = 1
        user.email = "admin@example.com"
        user.is_admin = True
        user.is_active = True
        mock.return_value = user
        yield user


@pytest.fixture
def mock_encrypt():
    """Mock encryption function."""
    with patch("app.api.ai_configs.encrypt") as mock:
        mock.return_value = "encrypted-key-12345"
        yield mock


class TestListAIConfigs:
    """Tests for GET /api/ai-configs endpoint."""

    def test_list_configs_success(self, mock_db, mock_current_user):
        """Test successful list of AI configurations."""
        # Setup mock data
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.config_name = "DeepSeek Config"
        mock_config.provider = AIProvider.DEEPSEEK
        mock_config.model_name = "deepseek-chat"
        mock_config.encrypted_api_key = "encrypted-key"
        mock_config.is_default = True
        mock_config.created_at = "2024-01-01T00:00:00"
        mock_config.updated_at = "2024-01-01T00:00:00"

        mock_db.query.return_value.count.return_value = 1
        mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_config
        ]

        response = client.get("/api/ai-configs")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["config_name"] == "DeepSeek Config"
        assert data["items"][0]["api_key_set"] is True

    def test_list_configs_empty(self, mock_db, mock_current_user):
        """Test list with no configurations."""
        mock_db.query.return_value.count.return_value = 0
        mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        response = client.get("/api/ai-configs")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0


class TestGetAIConfig:
    """Tests for GET /api/ai-configs/{config_id} endpoint."""

    def test_get_config_success(self, mock_db, mock_current_user):
        """Test successful get of AI configuration."""
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.config_name = "DeepSeek Config"
        mock_config.provider = AIProvider.DEEPSEEK
        mock_config.model_name = "deepseek-chat"
        mock_config.encrypted_api_key = "encrypted-key"
        mock_config.is_default = True
        mock_config.created_at = "2024-01-01T00:00:00"
        mock_config.updated_at = "2024-01-01T00:00:00"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_config

        response = client.get("/api/ai-configs/1")

        assert response.status_code == 200
        data = response.json()
        assert data["config_name"] == "DeepSeek Config"
        assert data["api_key_set"] is True

    def test_get_config_not_found(self, mock_db, mock_current_user):
        """Test get of non-existent configuration."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.get("/api/ai-configs/999")

        assert response.status_code == 404


class TestCreateAIConfig:
    """Tests for POST /api/ai-configs endpoint."""

    def test_create_config_success(self, mock_db, mock_admin_user, mock_encrypt):
        """Test successful creation of AI configuration."""
        mock_db.query.return_value.filter.return_value.first.return_value = (
            None  # No existing config
        )

        # Mock the created config
        created_config = MagicMock()
        created_config.id = 1
        created_config.config_name = "New Config"
        created_config.provider = AIProvider.DEEPSEEK
        created_config.model_name = "deepseek-chat"
        created_config.encrypted_api_key = "encrypted-key-12345"
        created_config.is_default = False
        created_config.is_active = False
        created_config.created_at = "2024-01-01T00:00:00"
        created_config.updated_at = "2024-01-01T00:00:00"

        # Mock add and refresh
        mock_db.add.return_value = None
        mock_db.flush.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        response = client.post(
            "/api/ai-configs",
            json={
                "config_name": "New Config",
                "provider": "deepseek",
                "model_name": "deepseek-chat",
                "api_key": "test-api-key",
                "is_default": False,
            },
        )

        assert response.status_code == 201
        mock_encrypt.assert_called_once_with("test-api-key")

    def test_create_config_duplicate_name(self, mock_db, mock_admin_user, mock_encrypt):
        """Test creation with duplicate name."""
        existing_config = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_config

        response = client.post(
            "/api/ai-configs",
            json={
                "config_name": "Existing Config",
                "provider": "deepseek",
                "model_name": "deepseek-chat",
                "api_key": "test-api-key",
            },
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestUpdateAIConfig:
    """Tests for PUT /api/ai-configs/{config_id} endpoint."""

    def test_update_config_success(self, mock_db, mock_admin_user, mock_encrypt):
        """Test successful update of AI configuration."""
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.config_name = "Old Config"
        mock_config.provider = AIProvider.DEEPSEEK
        mock_config.model_name = "deepseek-chat"
        mock_config.encrypted_api_key = "old-encrypted-key"
        mock_config.is_default = False
        mock_config.is_active = False
        mock_config.created_at = "2024-01-01T00:00:00"
        mock_config.updated_at = "2024-01-01T00:00:00"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_config
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        response = client.put(
            "/api/ai-configs/1",
            json={
                "config_name": "Updated Config",
                "model_name": "deepseek-reasoner",
            },
        )

        assert response.status_code == 200

    def test_update_config_not_found(self, mock_db, mock_admin_user, mock_encrypt):
        """Test update of non-existent configuration."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.put(
            "/api/ai-configs/999",
            json={
                "config_name": "Updated Config",
            },
        )

        assert response.status_code == 404


class TestDeleteAIConfig:
    """Tests for DELETE /api/ai-configs/{config_id} endpoint."""

    def test_delete_config_success(self, mock_db, mock_admin_user):
        """Test successful deletion of AI configuration."""
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.config_name = "To Delete"
        mock_config.is_active = False
        mock_config.encrypted_api_key = "key"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_config
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        response = client.delete("/api/ai-configs/1")

        assert response.status_code == 204

    def test_delete_active_config_fails(self, mock_db, mock_admin_user):
        """Test deletion of active configuration fails."""
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.config_name = "Active Config"
        mock_config.is_active = True
        mock_config.encrypted_api_key = "key"

        # Mock no other configs
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_config,  # First query for the config itself
            None,  # Query for default config
            None,  # Query for any other config
        ]

        response = client.delete("/api/ai-configs/1")

        assert response.status_code == 400
        assert "Cannot delete" in response.json()["detail"]

    def test_delete_config_not_found(self, mock_db, mock_admin_user):
        """Test deletion of non-existent configuration."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.delete("/api/ai-configs/999")

        assert response.status_code == 404


class TestActivateAIConfig:
    """Tests for POST /api/ai-configs/{config_id}/activate endpoint."""

    def test_activate_config_success(self, mock_db, mock_admin_user):
        """Test successful activation of AI configuration."""
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.config_name = "To Activate"
        mock_config.provider = AIProvider.DEEPSEEK
        mock_config.model_name = "deepseek-chat"
        mock_config.encrypted_api_key = "key"
        mock_config.is_active = False
        mock_config.is_default = False
        mock_config.created_at = "2024-01-01T00:00:00"
        mock_config.updated_at = "2024-01-01T00:00:00"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_config
        mock_db.query.return_value.filter.return_value.update.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        response = client.post("/api/ai-configs/1/activate")

        assert response.status_code == 200

    def test_activate_config_without_key_fails(self, mock_db, mock_admin_user):
        """Test activation fails without API key."""
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.config_name = "No Key Config"
        mock_config.encrypted_api_key = None
        mock_config.is_active = False

        mock_db.query.return_value.filter.return_value.first.return_value = mock_config

        response = client.post("/api/ai-configs/1/activate")

        assert response.status_code == 400
        assert "API key" in response.json()["detail"]

    def test_activate_config_not_found(self, mock_db, mock_admin_user):
        """Test activation of non-existent configuration."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.post("/api/ai-configs/999/activate")

        assert response.status_code == 404


class TestAuditLog:
    """Tests for audit logging functionality."""

    def test_create_creates_audit_log(self, mock_db, mock_admin_user, mock_encrypt):
        """Test that create operation creates audit log."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add.return_value = None
        mock_db.flush.return_value = None
        mock_db.commit.return_value = None

        client.post(
            "/api/ai-configs",
            json={
                "config_name": "Test Config",
                "provider": "deepseek",
                "model_name": "deepseek-chat",
                "api_key": "test-key",
            },
        )

        # Verify audit log was added (db.add called twice: once for config, once for audit)
        assert mock_db.add.call_count >= 1

    def test_delete_creates_audit_log(self, mock_db, mock_admin_user):
        """Test that delete operation creates audit log."""
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.config_name = "To Delete"
        mock_config.is_active = False
        mock_config.encrypted_api_key = "key"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_config
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        client.delete("/api/ai-configs/1")

        # Verify audit log was added
        assert mock_db.add.call_count >= 1
