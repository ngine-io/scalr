import os
import click
import yaml
import uvicorn

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from apscheduler.schedulers.background import BackgroundScheduler

from scalr.db import read_from_db
from scalr.version import __version__
from scalr.task import scale
from scalr.log import log

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
    config = os.getenv('SCALR_CONFIG', './config.yml')
    interval = int(os.getenv('SCALR_INTERVAL', 60))
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


def main():
    uvicorn.run(
        "scalr.app:app",
        host=os.getenv('SCALR_HOST', '127.0.0.1'),
        port=int(os.getenv('SCALR_PORT', 5000)),
        log_level="info"
    )


if __name__ == "__main__":
    main()
