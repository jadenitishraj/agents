# `logger/middleware.py` Explained

This file is responsible for intercepting API traffic around `/research`, measuring duration, logging request/response details, and rebuilding the response after reading its body.

## ASCII Tree of the File

```text
logger/
├── middleware.py
│   ├── import time
│   │   └── used to measure request duration
│   │
│   ├── from starlette.middleware.base import BaseHTTPMiddleware
│   │   └── provides the middleware base class
│   │
│   ├── from starlette.requests import Request
│   │   └── request object type for FastAPI/Starlette
│   │
│   ├── from starlette.responses import StreamingResponse
│   │   └── used to rebuild the response after body interception
│   │
│   ├── from logger.loki import logger
│   │   └── uses the shared logger created in loki.py
│   │
│   └── class LoggingMiddleware(BaseHTTPMiddleware)
│       └── async def dispatch(self, request, call_next)
│           ├── if not request.url.path.startswith("/research"):
│           │   └── skip logging logic for non-research routes
│           ├── logger.info("Incoming Request: ...")
│           ├── start_time = time.time()
│           ├── response = await call_next(request)
│           ├── response_body = b""
│           ├── async for chunk in response.body_iterator:
│           │   └── collect outgoing response bytes
│           ├── duration = time.time() - start_time
│           ├── logger.info("Outgoing Response: ...")
│           │   ├── status code
│           │   ├── duration
│           │   └── payload text
│           └── return StreamingResponse(...)
│               ├── iter([response_body])
│               ├── status_code=response.status_code
│               ├── headers=dict(response.headers)
│               └── media_type=response.media_type
```

## What the File Is Doing

This file does one job:

- wrap the request/response path so the app can observe API traffic

That makes it a natural observability point because every request passes through middleware before the response returns to the user.

## Important Vocabulary

### `middleware`

`Middleware` is code that sits between the incoming request and the outgoing response.

Why it is used:
- because it can observe both sides of the API exchange
- it is the perfect place to measure timing
- it is the perfect place to add request/response logging

### `dispatch`

`dispatch(...)` is the main method of this middleware.

This is where the file decides:

- whether to observe the request
- when timing starts
- when timing ends
- what gets logged

Why it is used:
- because middleware needs a single entry point for wrapping request handling

### `call_next`

`call_next(request)` means:

- "pass this request to the next layer of the application"

Why it is used:
- because middleware usually does something before and after the real endpoint runs

### `StreamingResponse`

`StreamingResponse` is used here to rebuild the response after its body was consumed.

Why it is used:
- because once the middleware reads the original response body iterator, it must reconstruct a usable response for the client

## Why the Path Filter Matters

This file begins with:

```python
if not request.url.path.startswith("/research"):
    return await call_next(request)
```

That means the extra logging logic only applies to `/research`.

Why this matters:

- it avoids unnecessary logging for unrelated routes
- it reduces noise
- it keeps the logging focused on the main research pipeline

This is a good example of intentional observability instead of logging everything blindly.

## Data Flow Inside This File

```text
Incoming HTTP Request
        │
        ▼
dispatch(request, call_next)
  ├── check request path
  ├── log incoming request
  ├── start timer
  ├── call_next(request)
  │     └── actual FastAPI endpoint runs
  ├── read outgoing response body
  ├── compute duration
  ├── log outgoing response
  └── rebuild response with StreamingResponse
        │
        ▼
Client receives final response
```

## Why the Response Rebuild Is Necessary

This is the most important implementation detail in the file.

The middleware loops through:

```python
async for chunk in response.body_iterator:
```

That consumes the original response body.

If the middleware did not rebuild the response afterward, the client could receive an empty or broken response.

So the `StreamingResponse(...)` at the end is not extra decoration.

It is necessary because:

- the middleware wanted to inspect the body
- but the client still needs that body

## What This File Gives Students

This file teaches a very practical systems lesson:

- observability is often inserted around an existing path, not inside business logic itself

The business logic answers the research question.
The middleware observes the API behavior around that logic.

## Where It Gets Used

This middleware is registered in:

- `backend/api.py`

So `backend/api.py` activates it, but `middleware.py` contains the actual interception logic.
