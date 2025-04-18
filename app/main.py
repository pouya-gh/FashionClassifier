from fastapi import FastAPI
from fastapi.security import APIKeyHeader
from fastapi import Security, HTTPException, status, Depends

from .database.db import get_db, Base, engine
from .database.models import APIKey

from .utils.auth import get_api_key, get_current_user

from .routes import classify, auth

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(classify.router)
app.include_router(auth.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    args = parser.parse_args()
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)
