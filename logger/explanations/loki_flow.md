# `logger/loki.py` Explained

This file is responsible for creating the project logger and, when credentials exist, attaching a Loki handler so logs can be pushed to Grafana Loki.

## ASCII Tree of the File

```text
logger/
├── loki.py
│   ├── import os
│   │   └── used to read environment variables
│   │
│   ├── import logging
│   │   └── used to create and configure the Python logger
│   │
│   ├── import logging_loki
│   │   └── provides LokiHandler for shipping logs to Grafana Loki
│   │
│   ├── def get_loki_logger(name="research")
│   │   ├── reads LOKI_URL
│   │   │   └── builds final push URL ending in /loki/api/v1/push
│   │   ├── reads LOKI_USER_ID
│   │   ├── reads LOKI_API_KEY
│   │   ├── logger = logging.getLogger(name)
│   │   ├── logger.setLevel(logging.INFO)
│   │   ├── if not logger.handlers:
│   │   │   ├── logging.basicConfig(level=logging.INFO)
│   │   │   └── prevents duplicate handler attachment on reload
│   │   ├── if LOKI_URL and LOKI_USER_ID and LOKI_API_KEY:
│   │   │   ├── loki_handler = logging_loki.LokiHandler(...)
│   │   │   │   ├── url=LOKI_URL
│   │   │   │   ├── tags={"application": "research-agents"}
│   │   │   │   ├── auth=(LOKI_USER_ID, LOKI_API_KEY)
│   │   │   │   └── version="1"
│   │   │   └── logger.addHandler(loki_handler)
│   │   └── return logger
│   │
│   └── logger = get_loki_logger()
│       └── exports a ready-to-use logger object
```

## What the File Is Doing

This file does one job:

- build a Python logger that can send logs to Loki

It does not decide:

- what request should be logged
- what response should be logged
- when timing should be measured

That work happens elsewhere.

This file only prepares the logging destination.

## Important Vocabulary

### `logger`

A `logger` is the object your code uses to emit log messages.

Examples:
- `logger.info(...)`
- `logger.error(...)`

Why it is used:
- because the app needs a standard way to record events

### `handler`

A `handler` is the part attached to a logger that decides where the logs go.

Examples:
- console
- file
- Loki

Why it is used:
- because one logger may send its messages to different destinations

### `LokiHandler`

`LokiHandler` is the bridge between normal Python logging and Grafana Loki.

Why it is used:
- because Python’s built-in logger does not know how to send logs to Loki by itself

## Why the `if not logger.handlers` Check Matters

This line is easy to miss, but it is important:

```python
if not logger.handlers:
```

Why it exists:

- if the app reloads
- or this module is imported more than once

without that check, multiple handlers could be attached to the same logger.

That would cause duplicate log entries.

So this small guard is protecting the system from repeated handler registration.

## Data Flow Inside This File

```text
Environment Variables
  ├── LOKI_URL
  ├── LOKI_USER_ID
  └── LOKI_API_KEY
          │
          ▼
get_loki_logger(...)
  ├── create logger
  ├── set INFO level
  ├── create LokiHandler if credentials exist
  └── attach handler to logger
          │
          ▼
exported logger object
```

## Why This File Matters

Without this file:

- the app could still run
- but Grafana Loki would not receive the project logs

So this file is the setup layer for log shipping.

It answers the question:

- "Where should our logs go?"

## Where It Gets Used

The exported `logger` is imported by:

- `backend/api.py`
- `logger/middleware.py`

That means those files produce the log messages, but `loki.py` makes sure there is a Loki destination ready to receive them.
