from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import jwt
from supabase import create_client
from models import LoginRequest, ChangePasswordRequest
from config import get_settings, Settings
from dependencies import require_session, get_user_from_session
from slowapi import Limiter
from slowapi.util import get_remote_address


limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")


def create_access_token(data: dict, settings: Settings) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def get_supabase_client(settings: Settings):
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    user = get_user_from_session(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    form = await request.form()
    email = str(form.get("email", "")).strip()
    password = str(form.get("password", "")).strip()

    if not email or not password:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Email y contraseña requeridos"},
            status_code=400,
        )

    try:
        supabase = get_supabase_client(settings)
        auth_response = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        user = auth_response.user
        if not user:
            raise HTTPException(status_code=401)

        role = user.user_metadata.get("role", "analyst")
        token = create_access_token(
            {"sub": user.id, "email": user.email, "role": role},
            settings,
        )

        redirect = RedirectResponse(url="/dashboard", status_code=302)
        redirect.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=settings.environment == "production",
            samesite="lax",
            max_age=settings.access_token_expire_minutes * 60,
        )
        return redirect

    except Exception:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Credenciales incorrectas"},
            status_code=401,
        )


@router.get("/logout")
async def logout() -> RedirectResponse:
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("access_token")
    return response


@router.get("/change-password", response_class=HTMLResponse)
async def change_password_page(
    request: Request,
    current_user: dict = Depends(require_session),
) -> HTMLResponse:
    return templates.TemplateResponse(
        "auth/change_password.html",
        {"request": request, "user": current_user},
    )


@router.post("/change-password")
async def change_password(
    request: Request,
    current_user: dict = Depends(require_session),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    form = await request.form()
    new_password = str(form.get("new_password", "")).strip()
    confirm_password = str(form.get("confirm_password", "")).strip()

    if not new_password or not confirm_password:
        return templates.TemplateResponse(
            "auth/change_password.html",
            {"request": request, "user": current_user, "error": "Todos los campos son requeridos"},
            status_code=400,
        )

    if new_password != confirm_password:
        return templates.TemplateResponse(
            "auth/change_password.html",
            {"request": request, "user": current_user, "error": "Las contraseñas no coinciden"},
            status_code=400,
        )

    if len(new_password) < 8:
        return templates.TemplateResponse(
            "auth/change_password.html",
            {"request": request, "user": current_user, "error": "La contraseña debe tener al menos 8 caracteres"},
            status_code=400,
        )

    try:
        supabase = get_supabase_client(settings)
        supabase.auth.admin.update_user_by_id(
            current_user["user_id"],
            {"password": new_password},
        )
        return templates.TemplateResponse(
            "auth/change_password.html",
            {"request": request, "user": current_user, "success": "Contraseña actualizada correctamente"},
        )
    except Exception:
        return templates.TemplateResponse(
            "auth/change_password.html",
            {"request": request, "user": current_user, "error": "Error al actualizar la contraseña"},
            status_code=500,
        )