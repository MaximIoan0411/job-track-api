from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.exceptions import ApplicationNotFoundError, InvalidStateError, VersionConflictError
from app.limiter import limiter
from app.routers import applications, auth

app = FastAPI(title="JobTrack API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(ApplicationNotFoundError)
async def application_not_found_handler(request: Request, exc: ApplicationNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(InvalidStateError)
async def invalid_state_handler(request: Request, exc: InvalidStateError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(VersionConflictError)
async def version_conflict_handler(request: Request, exc: VersionConflictError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


app.include_router(auth.router)
app.include_router(applications.router)