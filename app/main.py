from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from . import models
from .routes import health, waters, catches, claims, auth


Base.metadata.create_all(bind=engine)

app = FastAPI(title="FishClaim API", version="0.1.0")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health.router, prefix="/api")
app.include_router(waters.router, prefix="/api")
app.include_router(catches.router, prefix="/api")
app.include_router(claims.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

