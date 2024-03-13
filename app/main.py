from fastapi import FastAPI

from app.routes import routes

app = FastAPI()

app.include_router(routes.router)


@app.get("/health", tags=["Health Check"])
async def health_status():
    return {"message": "Application running"}
