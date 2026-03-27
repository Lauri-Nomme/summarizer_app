from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
from .config import settings
from .errors import AuthenticationError
from .summarizer.service import SummarizerService

router = APIRouter(prefix="/api", tags=["API"])
security = HTTPBearer()


class SummaryResponse(BaseModel):
    id: str
    summary: str
    summary_length: str
    source_type: str
    timestamp: str


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError()
        return user_id
    except JWTError:
        raise AuthenticationError()


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_endpoint(
    text: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    summary_length: str = Form("medium"),
    file: Optional[UploadFile] = File(None),
    user_id: str = Depends(verify_token),
):
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
        user_id=user_id,
    )
    return SummaryResponse(**record)


@router.post("/batch")
async def batch_summarize(
    files: List[UploadFile] = File(...),
    summary_length: str = Form("medium"),
    user_id: str = Depends(verify_token),
):
    files_data = []
    for file in files:
        file_bytes = await file.read()
        files_data.append((file_bytes, file.filename))

    return SummarizerService.batch_process(
        files_data=files_data,
        summary_length=summary_length,
        user_id=user_id,
    )


@router.get("/history")
async def get_history(user_id: str = Depends(verify_token)):
    return SummarizerService.get_history(user_id)
