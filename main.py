import traceback
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from chatbot_backend import my_client, my_model, chatbot_system_message, resume_obj
from jd_matcher import read_document, parse_jd, match_jd, format_report

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_SUFFIXES = (".pdf", ".docx")

app = FastAPI()

@app.get("/")
def home():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)


@app.post("/chat")
def chat(request: ChatRequest):
    messages = [chatbot_system_message] + [m.model_dump() for m in request.messages]

    def generate():
        try:
            stream = my_client.chat.completions.create(
                model=my_model, messages=messages, stream=True
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                piece = chunk.choices[0].delta.content
                if piece:
                    yield piece
        except Exception:
            # response already started, can't send an error code now
            traceback.print_exc()
            yield "\n\n[Something went wrong, please try again in a minute.]"

    return StreamingResponse(generate(), media_type="text/plain")


# name and project names for the frontend (no contact info)
@app.get("/meta")
def meta():
    return {
        "name": resume_obj.name,
        "projects": [p.name for p in resume_obj.projects][:4],
    }


@app.post("/upload-jd")
def upload_jd(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="Please upload a .pdf or .docx file.")

    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is too large (limit 5 MB).")

    try:
        jd_text = read_document(data, suffix)
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=422, detail="Could not read this file.")

    if not jd_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No readable text found. Scanned or image-only PDFs are not supported.",
        )

    try:
        jd = parse_jd(jd_text)
        result = match_jd(jd, resume_obj)
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=502, detail="Could not analyze this job description. Please try again."
        )

    return {"report": format_report(jd, result), "result": result.model_dump()}