from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.database import connect_db, close_db
from app.routers import auth, fields, sensors, decisions, dashboard_farmer, dashboard_admin
from app.services.admin_service import log_event
from app.middleware import ErrorHandlingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    await log_event("system", "سیستم با موفقیت راه‌اندازی شد")
    yield
    await close_db()


app = FastAPI(
    title="سیستم کشاورزی هوشمند دقیق",
    description="سیستم مدیریت هوشمند مزارع بر اساس داده‌های سنسور IoT",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

base_dir = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

app.add_middleware(ErrorHandlingMiddleware)

app.include_router(auth.router)
app.include_router(fields.router)
app.include_router(sensors.router)
app.include_router(decisions.router)
app.include_router(dashboard_farmer.router)
app.include_router(dashboard_admin.router)


@app.get("/", tags=["صفحه اصلی"])
async def root(request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/dashboard/farmer", tags=["صفحه اصلی"])
async def farmer_dashboard_page(request):
    return templates.TemplateResponse(request, "farmer_dashboard.html")


@app.get("/dashboard/admin", tags=["صفحه اصلی"])
async def admin_dashboard_page(request):
    return templates.TemplateResponse(request, "admin_dashboard.html")
