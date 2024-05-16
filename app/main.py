from fastapi import FastAPI

from app.routes import aoi, job, prediction_request, predictions, scl

app = FastAPI()

app.include_router(predictions.router)
app.include_router(prediction_request.router)
app.include_router(aoi.router)
app.include_router(job.router)
app.include_router(scl.router)


@app.get("/health", tags=["Health Check"])
async def health_status():
    return {"message": "Application running"}
