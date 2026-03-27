import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("ENV", "production") == "development"
    print(f"Starting GenAI Summarizer on {host}:{port} (reload={reload})")
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=reload)
