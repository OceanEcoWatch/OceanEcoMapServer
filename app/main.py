from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import aoi, job, model, predictions, scl

app = FastAPI()


origins = ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("CORS-Middleware active for origins: ", origins)

app.include_router(predictions.router)
app.include_router(aoi.router)
app.include_router(job.router)
app.include_router(scl.router)
app.include_router(model.router)


@app.get("/health", tags=["Health Check"])
async def health_status():
    return {"message": "Application running"}
