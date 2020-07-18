import os
import click
import yaml
import datetime

from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler

from scalr.db import read_from_db
from scalr.version import __version__
from scalr.task import scale

scheduler = BackgroundScheduler()

app = FastAPI(
    title="scalr",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    log.info("Scalr started")
    config = os.getenv('SCALR_CONFIG') or './config.yml'
    interval = int(os.getenv('SCALR_INTERVAL')) or 60
    log.info(f"interval is set to: {interval}")
    scheduler.add_job(scale, 'interval', [config, interval], seconds=interval, max_instances=1)
    scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    log.info("Scalr stopped")
    scheduler.shutdown(wait=False)

@app.get("/")
async def root():
    result = read_from_db()
    return result

@app.get("/version")
async def root():
    return { 'verison': __version__ }
