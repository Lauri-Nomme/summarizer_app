import os
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from .config import settings
from .summarizer.service import SummarizerService
from .logger import get_logger

router = APIRouter(tags=["UI"])

template_dir = os.path.join(
    os.path.dirname(__file__), "..", "..", "frontend", "templates"
)
templates = Jinja2Templates(directory=os.path.normpath(template_dir))

# In-memory session history for UI (simplified)
ui_history: list = []


def _base_context() -> dict:
    """Common template context with Azure OpenAI status."""
    return {
        "model_name": settings.AZURE_OPENAI_DEPLOYMENT or "(not set)",
        "azure_configured": settings.azure_openai_configured,
        "history": ui_history,
    }


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    ctx = {**_base_context(), "summary": None, "error": None,
           "input_text": "", "input_url": "", "selected_length": "medium"}
    return templates.TemplateResponse(request, "dashboard.html", context=ctx)


@router.post("/summarize", response_class=HTMLResponse)
async def ui_summarize(
    request: Request,
    text: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    summary_length: str = Form("medium"),
    file: Optional[UploadFile] = File(None),
):
    log = get_logger("ui_user")
    error = None
    summary = None

    try:
        file_bytes = None
        filename = None
        if file and file.filename:
            file_bytes = await file.read()
            filename = file.filename

        record = SummarizerService.process_and_summarize(
            content=text,
            file_bytes=file_bytes,
            filename=filename,
            url=url,
            summary_length=summary_length,
            user_id="ui_user",
        )
        summary = record["summary"]
        ui_history.insert(
            0,
            {
                "summary": summary,
                "length": summary_length,
                "source": filename or url or "text input",
            },
        )
        log.info("UI summarization successful")
    except Exception as e:
        error = str(e)
        log.error(f"UI summarization failed: {error}")

    ctx = {
        **_base_context(),
        "summary": summary,
        "error": error,
        "input_text": text or "",
        "input_url": url or "",
        "selected_length": summary_length,
    }
    return templates.TemplateResponse(request, "dashboard.html", context=ctx)


@router.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    return templates.TemplateResponse(
        request, "history.html", context={"history": ui_history}
    )
