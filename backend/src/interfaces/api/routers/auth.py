from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.auth_service import AuthApplicationService
from src.domains.audit.services import AuditService
from src.domains.auth.services import AuthDomainService
from src.infrastructure.db.repositories.user_repo import UserRepository
from src.interfaces.api.dependencies import get_current_user, get_db
from src.interfaces.api.schemas.auth_schemas import (
    LoginRequest,
    LoginResponse,
    RefreshResponse,
    UserResponse,
)

router = APIRouter()


def _build_service(db: AsyncSession) -> AuthApplicationService:
    from src.infrastructure.db.repositories.audit_repo import AuditRepository
    return AuthApplicationService(
        user_repo=UserRepository(db),
        auth_domain=AuthDomainService(),
        audit=AuditService(AuditRepository(db)),
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    svc = _build_service(db)
    result = await svc.login(
        username=body.username,
        password=body.password,
        response=response,
        ip_address=request.client.host if request.client else None,
    )
    return LoginResponse(
        access_token=result["access_token"],
        user=UserResponse(
            id=result["user"].id,
            username=result["user"].username,
            role=result["user"].role.value,
            display_name=result["user"].display_name,
        ),
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(request: Request, db: AsyncSession = Depends(get_db)):
    refresh_token = request.cookies.get("clinic_session")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")
    svc = _build_service(db)
    access_token = await svc.refresh(refresh_token)
    return RefreshResponse(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from src.interfaces.api.dependencies import bearer_scheme
    credentials = await bearer_scheme(request)
    from src.domains.auth.value_objects import Token
    payload = Token.decode(credentials.credentials)
    jti = payload.get("jti", "")
    svc = _build_service(db)
    await svc.logout(jti=jti, actor_id=current_user.id)
    response.delete_cookie("clinic_session", path="/api/v1/auth/refresh")


@router.get("/me", response_model=UserResponse)
async def me(current_user=Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        display_name=current_user.display_name,
    )
