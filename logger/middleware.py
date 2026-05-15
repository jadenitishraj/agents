import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import StreamingResponse
from logger.loki import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Ignore static files to prevent breaking the frontend stream
        if not request.url.path.startswith("/research"):
            return await call_next(request)
            
        logger.info(f"Incoming Request: {request.method} {request.url.path}")
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        
        # Intercept and log outgoing response
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        
        duration = time.time() - start_time
        logger.info(f"Outgoing Response: {response.status_code} Duration: {duration:.2f}s Payload: {response_body.decode('utf-8')}")
        
        return StreamingResponse(
            iter([response_body]),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )
