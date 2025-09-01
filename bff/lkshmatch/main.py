import asyncio
import logging
from types import TracebackType
from typing import Self, Literal

import uvicorn
import uvloop
from fastapi import FastAPI

from lkshmatch.tg_bot.bot import bot
from lkshmatch.website.activities import activities_router
from lkshmatch.website.activities_gsheets import table_adapter_router
from lkshmatch.website.api_requests import api_requests_router
from lkshmatch.website.auth.auth import auth_router
from lkshmatch.website.auth.login_middleware import LoginWallMiddleware


class Runner:
    @staticmethod
    def start_app() -> None:
        app = FastAPI(
            title="Match REST API",
            summary="REST API documentation for Match",
            version="0.1.0",
            docs_url="/",
        )
        app.include_router(activities_router)
        app.include_router(auth_router)
        app.include_router(table_adapter_router)
        app.include_router(api_requests_router)

        app.add_middleware(LoginWallMiddleware)

        uvicorn.run(
            app=app,
            host="0.0.0.0",
            port=80,
            workers=1,
            log_config="logging.ini",
            log_level="debug",
        )

    @staticmethod
    async def start_bot(bot_logger: logging.Logger) -> None:
        uvloop.install()

        try:
            bot_logger.info("Starting Telegram bot...")
            await bot.polling(non_stop=True)
        except KeyboardInterrupt:
            return

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[Exception] | None,
        exc_val: Exception | None,
        exc_tb: TracebackType | None,
    ) -> None | Literal[True]:
        if isinstance(exc_val, KeyboardInterrupt):
            return True
        return None


if __name__ == "__main__":
    logging.basicConfig(filename="logging.ini", level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    with Runner() as runner:
        loop.run_in_executor(None, runner.start_bot, logger)
        loop.run_in_executor(None, runner.start_app)
