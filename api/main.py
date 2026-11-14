"""HTTP API for the PWA. POST /compare runs the engine; nothing is stored.

CORS: set ALLOWED_ORIGINS (comma separated) for the deployed PWA. Default is open, which is fine for a demo only.
"""
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, model_validator

from engine.compare import Engine
from engine.coverage import presets
from engine.strategies import EXISTING

app = FastAPI(title="Field Shift engine", version="0.1")
origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",")]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])
engine = Engine.from_repo()


class CompareRequest(BaseModel):
    location: str | None = None
    lat: float | None = None
    lon: float | None = None
    current_rotation: str = "soybean_fallow"
    water_source: str = "rainfed"
    priorities: list[str] = []
    constraints: dict = {}

    @model_validator(mode="after")
    def check(self):
        if self.location is None and (self.lat is None or self.lon is None):
            raise ValueError("give either a location name or both lat and lon")
        if self.location is not None and self.location not in presets():
            raise ValueError(f"unknown location: {self.location}")
        if self.current_rotation not in EXISTING:
            raise ValueError(f"unknown current_rotation: {self.current_rotation}")
        return self


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/compare")
def compare(req: CompareRequest):
    try:
        return engine.compare(req.model_dump())
    except ValueError as e:  # e.g. an unknown priority
        raise HTTPException(status_code=422, detail=str(e))
