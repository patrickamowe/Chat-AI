from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

static_dir = "frontend/static"
templates_dir = "frontend/templates"

app = FastAPI()

# Mount the 'static' folder to serve CSS and JS
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Point to the 'templates' folder for HTML
templates = Jinja2Templates(directory=templates_dir)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):

    # Render home-page.html from the templates folder
    return templates.TemplateResponse(name="home-page.html", request=request, context={})


@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):

    # Render profile-page.html from the templates folder
    return templates.TemplateResponse(name="profile-page.html", request=request, context={})