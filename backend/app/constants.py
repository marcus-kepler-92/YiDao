"""
Application constants and enumerations

Centralized location for all constants, magic strings, and enums.
"""

from enum import Enum

# =============================================================================
# Application Constants
# =============================================================================

APP_VERSION = "1.0.0"
# Note: Use settings.api_prefix_v1 for API prefix configuration


# =============================================================================
# Pagination
# =============================================================================

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1


# =============================================================================
# Cache
# =============================================================================


class CacheTTL:
    """Cache TTL constants (in seconds)"""

    SHORT = 60  # 1 minute
    MEDIUM = 300  # 5 minutes
    LONG = 3600  # 1 hour
    DAY = 86400  # 24 hours


class CachePrefix:
    """Cache key prefixes"""

    USER = "user"
    SESSION = "session"
    RATE_LIMIT = "rate_limit"


# =============================================================================
# User Status
# =============================================================================


class UserStatus(str, Enum):
    """User account status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


# =============================================================================
# Audit Actions
# =============================================================================


class AuditAction(str, Enum):
    """Audit log action types"""

    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    UPLOAD = "UPLOAD"
    DOWNLOAD = "DOWNLOAD"


# =============================================================================
# HTTP Headers
# =============================================================================


class Headers:
    """Custom HTTP header names"""

    TRACE_ID = "X-Trace-Id"
    REQUEST_ID = "X-Request-Id"
    RATE_LIMIT_LIMIT = "X-RateLimit-Limit"
    RATE_LIMIT_REMAINING = "X-RateLimit-Remaining"
    RATE_LIMIT_RESET = "X-RateLimit-Reset"


# =============================================================================
# Error Codes
# =============================================================================


class ErrorCode:
    """Application error codes"""

    # General
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    BAD_REQUEST = "BAD_REQUEST"

    # Auth
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_TOKEN = "INVALID_TOKEN"

    # User
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    USERNAME_ALREADY_EXISTS = "USERNAME_ALREADY_EXISTS"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"

    # Rate Limit
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


# =============================================================================
# Messages (Chinese)
# =============================================================================


class Messages:
    """User-facing messages"""

    # Success
    CREATE_SUCCESS = "创建成功"
    UPDATE_SUCCESS = "更新成功"
    DELETE_SUCCESS = "删除成功"
    RESTORE_SUCCESS = "恢复成功"

    # Errors
    USER_NOT_FOUND = "用户不存在"
    EMAIL_EXISTS = "邮箱已被注册"
    USERNAME_EXISTS = "用户名已被使用"
    INVALID_CREDENTIALS = "用户名或密码错误"
    UNAUTHORIZED = "请先登录"
    FORBIDDEN = "权限不足"
    RATE_LIMIT_EXCEEDED = "请求过于频繁，请稍后重试"
    INTERNAL_ERROR = "服务器内部错误"
