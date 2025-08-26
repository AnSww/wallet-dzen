import logging, traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("errors")


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    log.warning("HTTP %s at %s -> %s", exc.status_code, request.url.path, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def unhandled_error_handler(request: Request, exc: Exception):
    log.error("Unhandled error at %s\n%s", request.url.path, traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": "internal error"})
