import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

from studob.api.dependencies import AppContext
from studob.config.loader import get_config
from studob.logging_setup import get_logger, setup_logging


async def bootstrap(settings):
    setup_logging(settings.app.log_level)
    logger = get_logger("bootstrap")

    context = AppContext()
    await context.initialize(settings)

    logger.info("Services initialized")
    return context


async def main():
    settings = get_config()
    await bootstrap(settings)

    logger = get_logger("main")
    logger.info(f"Starting server on {settings.app.host}:{settings.app.port}")

    config = uvicorn.Config(
        "studob.api.app:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
