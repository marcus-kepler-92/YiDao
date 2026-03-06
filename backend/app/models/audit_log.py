"""
审计日志模型

记录用户操作：谁、什么时间、对什么资源、做了什么操作
"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from app.core.database import Base


class AuditLog(Base):
    """审计日志模型"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # 操作者信息
    user_id = Column(Integer, nullable=True, index=True)  # 用户 ID（未登录为 None）
    username = Column(String(50), nullable=True)  # 用户名
    ip_address = Column(String(45), nullable=True)  # IP 地址（支持 IPv6）
    user_agent = Column(String(500), nullable=True)  # User-Agent

    # 操作信息
    action = Column(
        String(50), nullable=False, index=True
    )  # 操作类型：CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT
    resource_type = Column(String(50), nullable=False, index=True)  # 资源类型：user, order, product
    resource_id = Column(String(100), nullable=True, index=True)  # 资源 ID
    resource_name = Column(String(200), nullable=True)  # 资源名称/描述

    # 请求信息
    method = Column(String(10), nullable=True)  # HTTP 方法
    path = Column(String(500), nullable=True)  # 请求路径
    query_params = Column(Text, nullable=True)  # 查询参数
    request_body = Column(Text, nullable=True)  # 请求体（脱敏后）

    # 响应信息
    status_code = Column(Integer, nullable=True)  # 响应状态码
    response_time_ms = Column(Integer, nullable=True)  # 响应时间（毫秒）

    # 变更详情
    old_values = Column(JSON, nullable=True)  # 变更前的值
    new_values = Column(JSON, nullable=True)  # 变更后的值

    # 追踪信息
    trace_id = Column(String(32), nullable=True, index=True)  # 链路追踪 ID
    span_id = Column(String(16), nullable=True)  # Span ID

    # 其他
    extra = Column(JSON, nullable=True)  # 额外信息
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return (
            f"<AuditLog {self.action} {self.resource_type}:{self.resource_id} "
            f"by user:{self.user_id}>"
        )
