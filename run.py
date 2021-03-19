import asyncio
import logging
import os
import signal
import sys

from app import create_app

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

log_level = os.environ.get("LOG_LEVEL", "INFO")
logging.basicConfig(level=log_level)
if log_level != "DEBUG":
    logging.getLogger('gino.engine._SAEngine').setLevel(logging.WARNING)


def main():
    access_logger = logging.getLogger("aiohttp.access")
    if "win" in sys.platform:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = create_app()
    # app.before_request(set_schema)
    app.run(access_log=access_logger)


if __name__ == "__main__":
    main()