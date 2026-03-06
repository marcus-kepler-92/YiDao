"""
API tests for user endpoints
"""


class TestUserEndpoints:
    """Tests for /api/v1/users endpoints"""

    def test_create_user(self, client_with_mocked_service, sample_user_data):
        """POST /api/v1/users - should create user"""
        response = client_with_mocked_service.post("/api/v1/users", json=sample_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "创建成功"
        assert "data" in data

    def test_create_user_invalid_email(self, client_with_mocked_service):
        """POST /api/v1/users - should reject invalid email"""
        response = client_with_mocked_service.post(
            "/api/v1/users",
            json={"username": "testuser", "email": "invalid-email", "password": "password123"},
        )

        assert response.status_code == 422

    def test_create_user_missing_fields(self, client_with_mocked_service):
        """POST /api/v1/users - should reject missing required fields"""
        response = client_with_mocked_service.post("/api/v1/users", json={"username": "testuser"})

        assert response.status_code == 422

    def test_get_user(self, client_with_mocked_service):
        """GET /api/v1/users/{id} - should get user by ID"""
        response = client_with_mocked_service.get("/api/v1/users/1")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_get_user_list(self, client_with_mocked_service):
        """GET /api/v1/users - should get paginated user list"""
        response = client_with_mocked_service.get("/api/v1/users")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "list" in data["data"]
        assert "total" in data["data"]
        assert "current" in data["data"]
        assert "pageSize" in data["data"]

    def test_get_user_list_with_pagination(self, client_with_mocked_service):
        """GET /api/v1/users - should accept pagination params"""
        response = client_with_mocked_service.get(
            "/api/v1/users", params={"current": 2, "pageSize": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["current"] == 2
        assert data["data"]["pageSize"] == 5

    def test_get_user_list_invalid_pagination(self, client_with_mocked_service):
        """GET /api/v1/users - should reject invalid pagination"""
        response = client_with_mocked_service.get(
            "/api/v1/users",
            params={"current": 0},  # current must be >= 1
        )

        assert response.status_code == 422

    def test_get_user_list_with_date_filters(self, client_with_mocked_service):
        """GET /api/v1/users - should filter by created_at range"""
        response = client_with_mocked_service.get(
            "/api/v1/users",
            params={
                "created_at_start": "2024-01-01T00:00:00Z",
                "created_at_end": "2024-12-31T23:59:59Z",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_get_user_list_with_username_search(self, client_with_mocked_service):
        """GET /api/v1/users - should search by username"""
        response = client_with_mocked_service.get("/api/v1/users", params={"username": "admin"})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_user_list_with_email_search(self, client_with_mocked_service):
        """GET /api/v1/users - should search by email"""
        response = client_with_mocked_service.get("/api/v1/users", params={"email": "example.com"})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_user_list_with_is_active_filter(self, client_with_mocked_service):
        """GET /api/v1/users - should filter by is_active status"""
        response = client_with_mocked_service.get("/api/v1/users", params={"is_active": "true"})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_user_list_with_sorting(self, client_with_mocked_service):
        """GET /api/v1/users - should sort by created_at descending"""
        response = client_with_mocked_service.get(
            "/api/v1/users", params={"sort_by": "created_at", "sort_order": "desc"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_user_list_with_ascending_sort(self, client_with_mocked_service):
        """GET /api/v1/users - should sort ascending"""
        response = client_with_mocked_service.get(
            "/api/v1/users", params={"sort_by": "username", "sort_order": "asc"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_user_list_with_combined_filters(self, client_with_mocked_service):
        """GET /api/v1/users - should work with multiple filters"""
        response = client_with_mocked_service.get(
            "/api/v1/users",
            params={
                "created_at_start": "2024-01-01T00:00:00Z",
                "created_at_end": "2024-12-31T23:59:59Z",
                "username": "test",
                "is_active": "true",
                "sort_by": "updated_at",
                "sort_order": "desc",
                "current": 1,
                "pageSize": 20,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["current"] == 1
        assert data["data"]["pageSize"] == 20

    def test_get_user_list_with_updated_at_filters(self, client_with_mocked_service):
        """GET /api/v1/users - should filter by updated_at range"""
        response = client_with_mocked_service.get(
            "/api/v1/users",
            params={
                "updated_at_start": "2024-01-01T00:00:00Z",
                "updated_at_end": "2024-12-31T23:59:59Z",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_user_list_invalid_date_format(self, client_with_mocked_service):
        """GET /api/v1/users - should reject invalid date format"""
        response = client_with_mocked_service.get(
            "/api/v1/users", params={"created_at_start": "invalid-date"}
        )

        # FastAPI should return 422 for invalid date format
        assert response.status_code == 422

    def test_get_user_list_invalid_sort_field(self, client_with_mocked_service):
        """GET /api/v1/users - should accept any sort_by (validation happens in service)"""
        # Note: API accepts any string, validation happens in service/repository layer
        response = client_with_mocked_service.get(
            "/api/v1/users", params={"sort_by": "invalid_field"}
        )

        # API accepts it, but repository will default to "id"
        assert response.status_code == 200

    def test_update_user(self, client_with_mocked_service):
        """PUT /api/v1/users/{id} - should update user"""
        response = client_with_mocked_service.put(
            "/api/v1/users/1", json={"username": "updateduser"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "更新成功"

    def test_delete_user(self, client_with_mocked_service):
        """DELETE /api/v1/users/{id} - should soft delete user"""
        response = client_with_mocked_service.delete("/api/v1/users/1")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "删除成功"

    def test_restore_user(self, client_with_mocked_service):
        """POST /api/v1/users/{id}/restore - should restore deleted user"""
        response = client_with_mocked_service.post("/api/v1/users/1/restore")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "恢复成功"

    def test_get_deleted_users(self, client_with_mocked_service):
        """GET /api/v1/users/deleted - should get deleted users"""
        response = client_with_mocked_service.get("/api/v1/users/deleted")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data


class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_health_check(self, client):
        """GET /health - should return ok status"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_root_endpoint(self, client):
        """GET / - should return app info"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data
        assert "version" in data
        assert "environment" in data

    def test_ready_endpoint(self, client):
        """GET /ready - should return readiness status"""
        response = client.get("/ready")

        # May return 200 or 503 depending on DB/Redis availability
        assert response.status_code in [200, 503]
        data = response.json()
        assert "ready" in data
        assert "status" in data
        assert "components" in data


class TestDocsEndpoint:
    """Tests for API documentation endpoints"""

    def test_docs_available(self, client):
        """GET /docs - should return Swagger UI"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema(self, client):
        """GET /openapi.json - should return OpenAPI schema"""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
