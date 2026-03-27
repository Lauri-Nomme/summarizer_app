from fastapi import FastAPI
from .api import router as api_router
from .ui import router as ui_router
from .errors import SummarizerError, summarizer_error_handler
from .logger import get_logger

logger = get_logger()


def create_app() -> FastAPI:
    app = FastAPI(
        title="GenAI Summarizer",
        description=(
            "A self-hosted application that summarizes text documents, "
            "web pages, and user input."
        ),
        version="1.0.0",
    )

    app.add_exception_handler(SummarizerError, summarizer_error_handler)
    app.include_router(api_router)
    app.include_router(ui_router)

    logger.info("GenAI Summarizer application initialized")
    return app


app = create_app()
