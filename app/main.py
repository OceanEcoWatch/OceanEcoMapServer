from fastapi import FastAPI

from app.routes import prediction_request, predictions

app = FastAPI()

app.include_router(predictions.router)
app.include_router(prediction_request.router)


@app.get("/health", tags=["Health Check"])
async def health_status():
    return {"message": "Application running"}
