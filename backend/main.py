from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

import pandas as pd
import io

from eda_engine import perform_eda

app = FastAPI()

# STATIC FILES
app.mount("/static", StaticFiles(directory="static"), name="static")

# HTML TEMPLATE
templates = Jinja2Templates(directory="templates")


# -------------------------
# HOME PAGE
# -------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


# -------------------------
# FILE UPLOAD API
# -------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    content = await file.read()

    filename = file.filename.lower()

    try:
        # CSV
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))

        # EXCEL
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(content))

        # XML
        elif filename.endswith(".xml"):
            df = pd.read_xml(io.BytesIO(content))

        else:
            return {"error": "Unsupported file format"}

        eda_result = perform_eda(df)

        return eda_result

    except Exception as e:
        return {"error": str(e)}
