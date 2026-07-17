from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend.routes.user import router as user_router
from backend.routes.auth import router as auth_router
from backend.routes.chat import router as chat_router
from backend.schemas.base import APIFailureSchema

static_dir = "frontend/static"
templates_dir = "frontend/templates"

app = FastAPI()

# Define the origins that are allowed to talk to your backend
origins = [
    "http://127.0.0.1:8000",  # Your local address
    "http://localhost:8000",
]

# Add the middleware to your FastAPI application
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
app.include_router(chat_router)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """
    Global handler to catch all HTTPExceptions and format them
    using the standardized APIFailureSchema.
    """
    schema = APIFailureSchema(
        status_code=exc.status_code,
        success=False,
        message=str(exc.detail)
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=schema.model_dump()
    )

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):

    # Render home-page.html from the templates folder
    return templates.TemplateResponse(name="home-page.html", request=request, context={})


@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):

    # Render profile-page.html from the templates folder
    return templates.TemplateResponse(name="profile-page.html", request=request, context={})