from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend.routes.user_route import router as user_router
from backend.routes.auth_route import router as auth_router
from backend.db.database import Base, engine

static_dir = "frontend/static"
templates_dir = "frontend/templates"

# Tell SQLAlchemy to physically create the tables now
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 1. Define the origins that are allowed to talk to your backend
origins = [
    "http://127.0.0.1:8000",  # Your local address
    "http://localhost:8000",
]

# 2. Add the middleware to your FastAPI application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # Allows your frontend origins
    allow_credentials=True,
    allow_methods=["*"],            # Allows POST, GET, OPTIONS, etc.
    allow_headers=["*"],            # Allows Authorization and Content-Type headers
)

# Mount the 'static' folder to serve CSS and JS
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Point to the 'templates' folder for HTML
templates = Jinja2Templates(directory=templates_dir)


# Routes
app.include_router(auth_router)
app.include_router(user_router)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):

    # Render home-page.html from the templates folder
    return templates.TemplateResponse(name="home-page.html", request=request, context={})


@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):

    # Render profile-page.html from the templates folder
    return templates.TemplateResponse(name="profile-page.html", request=request, context={})