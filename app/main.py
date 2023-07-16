from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

import socket

from .my_metrics import heads_count

app = FastAPI()

instrument = Instrumentator(excluded_handlers=["docs", ".*openapi.*", "/metrics"],)

app_instrument = instrument.instrument(app)

app_instrument.expose(app, include_in_schema=False, should_gzip=True)

@app.get("/")
async def root(example):
    heads_count.inc(10)
    return str(socket.gethostname())