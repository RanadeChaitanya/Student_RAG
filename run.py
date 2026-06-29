import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from suraj_dada.config.loader import get_config
from suraj_dada.logging_setup import setup_logging, get_logger
from suraj_dada.api.dependencies import AppContext
import uvicorn


async def bootstrap(settings):
    setup_logging(settings.app.log_level)
    logger = get_logger("bootstrap")

    context = AppContext()
    await context.initialize(settings)

    logger.info("Services initialized")
    return context


async def main():
    settings = get_config()
    context = await bootstrap(settings)

    logger = get_logger("main")
    logger.info(f"Starting server on {settings.app.host}:{settings.app.port}")

    config = uvicorn.Config(
        "suraj_dada.api.app:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
