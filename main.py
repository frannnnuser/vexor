from contextlib import contextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlmodel import Session, create_engine, SQLModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config import get_settings
from ml_engine import engine as ml_engine
from routers import auth, dashboard, predict, training, history, audit


settings = get_settings()
db_engine = create_engine(settings.database_url, echo=False)


def create_db_tables() -> None:
    SQLModel.metadata.create_all(db_engine)


@contextmanager
def get_db_session():
    with Session(db_engine) as session:
        yield session


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Vexor",
    description="Plataforma de prediccion binaria con Machine Learning",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(predict.router)
app.include_router(training.router)
app.include_router(history.router)
app.include_router(audit.router)


@app.on_event("startup")
async def startup_event() -> None:
    create_db_tables()
    ml_engine.load()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> RedirectResponse:
    return RedirectResponse(url="/auth/login", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_redirect(request: Request) -> RedirectResponse:
    return RedirectResponse(url="/dashboard/", status_code=302)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc) -> HTMLResponse:
    return templates.TemplateResponse(
        "pages/error.html",
        {"request": request, "code": 404, "message": "Pagina no encontrada"},
        status_code=404,
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc) -> HTMLResponse:
    return templates.TemplateResponse(
        "pages/error.html",
        {"request": request, "code": 500, "message": "Error interno del servidor"},
        status_code=500,
    )


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc) -> HTMLResponse:
    return templates.TemplateResponse(
        "pages/error.html",
        {"request": request, "code": 403, "message": "Acceso denegado"},
        status_code=403,
    )