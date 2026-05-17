import os
import uuid
from datetime import timedelta

from fastapi import HTTPException, Response, status

from src.domains.auth.entities import User, UserRole
from src.domains.auth.repository import IUserRepository
from src.domains.auth.services import AuthDomainService
from src.domains.auth.value_objects import Password, Token
from src.domains.audit.entities import AuditAction, AuditOutcome
from src.domains.audit.services import AuditService


class AuthApplicationService:
    def __init__(
        self,
        user_repo: IUserRepository,
        auth_domain: AuthDomainService,
        audit: AuditService,
    ) -> None:
        self._users = user_repo
        self._auth = auth_domain
        self._audit = audit

    async def login(
        self,
        username: str,
        password: str,
        response: Response,
        ip_address: str | None = None,
    ) -> dict:
        user = await self._users.find_by_username(username)
        if not user or not self._auth.verify_password(password, user.password_hash):
            await self._audit.log(
                action=AuditAction.USER_LOGIN,
                resource_type="User",
                outcome=AuditOutcome.FAILURE,
                ip_address=ip_address,
                detail={"reason": "invalid_credentials"},
            )
            # Generic message to not reveal whether username exists
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
            )

        access_token, jti = self._auth.create_access_token(user.id, user.role.value)
        device_id = str(uuid.uuid4())
        refresh_token = self._auth.create_refresh_token(user.id, device_id)

        expire_days = int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        response.set_cookie(
            key="clinic_session",
            value=refresh_token,
            httponly=True,
            secure=os.environ.get("ENVIRONMENT", "development") == "production",
            samesite="strict",
            max_age=expire_days * 86400,
            path="/api/v1/auth/refresh",
        )

        await self._audit.log(
            action=AuditAction.USER_LOGIN,
            resource_type="User",
            outcome=AuditOutcome.SUCCESS,
            actor_id=user.id,
            actor_role=user.role.value,
            resource_id=user.id,
            ip_address=ip_address,
        )

        return {"access_token": access_token, "user": user}

    async def logout(self, jti: str, actor_id: uuid.UUID | None = None) -> None:
        expire_minutes = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        await self._auth.blacklist_token(jti, ttl_seconds=expire_minutes * 60)
        await self._audit.log(
            action=AuditAction.USER_LOGOUT,
            resource_type="User",
            outcome=AuditOutcome.SUCCESS,
            actor_id=actor_id,
        )

    async def refresh(self, refresh_token: str) -> str:
        try:
            payload = Token.decode(refresh_token)
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")

        user_id = uuid.UUID(payload["sub"])
        user = await self._users.find_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        access_token, _ = self._auth.create_access_token(user.id, user.role.value)
        return access_token
