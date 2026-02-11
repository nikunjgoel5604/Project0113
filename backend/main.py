from fastapi import FastAPI, UploadFile, File
import pandas as pd
import io

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Nikunj Data Analyzer Backend Running"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    try:
        # Read file content safely
        contents = await file.read()

        # Convert bytes to string buffer
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

        return {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns)
        }

    except Exception as e:
        return {"error": str(e)}
