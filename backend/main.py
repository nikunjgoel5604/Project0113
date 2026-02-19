from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import pandas as pd
import io
import os

# =====================================================
# SMART IMPORT (Works Local + Render)
# =====================================================
try:
    from backend.eda_engine import perform_eda  # Render
except:
    from eda_engine import perform_eda  # Local


# =====================================================
# FASTAPI APP
# =====================================================
app = FastAPI()


# =====================================================
# BASE DIRECTORY
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# =====================================================
# STATIC FILES (CSS / JS)
# =====================================================
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)


# =====================================================
# TEMPLATES
# =====================================================
templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "templates")
)


# =====================================================
# HOME ROUTE
# =====================================================
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


# =====================================================
# FILE UPLOAD + EDA
# =====================================================
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    try:
        contents = await file.read()

        # ---------- CSV ----------
        if file.filename.lower().endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))

        # ---------- EXCEL ----------
        elif file.filename.lower().endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(contents))

        else:
            return JSONResponse(
                status_code=400,
                content={"error": "Unsupported file type"}
            )

        # ---------- RUN EDA ----------
        eda_result = perform_eda(df)

        return eda_result

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# =====================================================
# RUN (LOCAL ONLY)
# =====================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
