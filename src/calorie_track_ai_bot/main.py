from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1 import auth, estimates, health, meals, photos

app = FastAPI(title="Calories Count API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(photos.router, prefix="/api/v1", tags=["photos"])
app.include_router(estimates.router, prefix="/api/v1", tags=["estimates"])
app.include_router(meals.router, prefix="/api/v1", tags=["meals"])
