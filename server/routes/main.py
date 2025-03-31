from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()

# Set up templates
templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app/templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Home"})

@router.get("/health")
async def health():
    return {"status": "ok"}
