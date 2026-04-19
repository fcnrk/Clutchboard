from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_pool, close_pool
from app.routers import events, players, matches, weapons, utility


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_pool()
    yield
    await close_pool()


app = FastAPI(title="Clutchboard API", lifespan=lifespan)

if settings.debug:
    origins = ["*"]
elif settings.domain:
    origins = [f"https://{settings.domain}"]
else:
    origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "DELETE"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(players.router, prefix="/api")
app.include_router(matches.router, prefix="/api")
app.include_router(weapons.router, prefix="/api")
app.include_router(utility.router, prefix="/api")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
