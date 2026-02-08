from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.types import Receive, Scope, Send

import game_runtime as rt
from routers.combat import router as combat_router
from routers.equipment import router as equipment_router
from routers.gladiator import router as gladiator_router
from routers.pvp import router as pvp_router
from routers.system import router as system_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    rt._init_db()
    yield


app = FastAPI(title="Gladiator Arena API", version="1.0.0", lifespan=lifespan)


class StripApiPrefixMiddleware:
    """Allow Firebase /api/* rewrites by stripping the /api prefix."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            if path == "/api" or path.startswith("/api/"):
                new_path = path[4:] or "/"
                scope = dict(scope)
                scope["path"] = new_path
                if "raw_path" in scope:
                    raw_path = scope["raw_path"]
                    scope["raw_path"] = raw_path[4:] or b"/"
        await self.app(scope, receive, send)


app.add_middleware(StripApiPrefixMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(system_router)
app.include_router(gladiator_router)
app.include_router(combat_router)
app.include_router(pvp_router)
app.include_router(equipment_router)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc}"},
    )


@app.exception_handler(FastAPIRequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"Validation error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )
