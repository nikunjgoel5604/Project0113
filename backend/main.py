from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import pandas as pd
import io
from pathlib import Path

from eda_engine import run_eda


# ---------------------------------------------------
# BASE DIRECTORY
# ---------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------
# FASTAPI APP
# ---------------------------------------------------
app = FastAPI()


# ---------------------------------------------------
# STATIC FILES
# ---------------------------------------------------
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)


# ---------------------------------------------------
# HTML TEMPLATES
# ---------------------------------------------------
templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


# ---------------------------------------------------
# HOME PAGE
# ---------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


# ---------------------------------------------------
# FILE UPLOAD API
# ---------------------------------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    try:
        contents = await file.read()
        filename = file.filename.lower()

        # ---------- CSV ----------
        if filename.endswith(".csv"):
            df = pd.read_csv(
                io.StringIO(contents.decode("utf-8"))
            )

        # ---------- EXCEL ----------
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(
                io.BytesIO(contents)
            )

        else:
            return {"error": "Unsupported file type"}

        # RUN EDA ENGINE
        result = run_eda(df)

        return result

    except Exception as e:
        return {"error": str(e)}
