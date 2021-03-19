from pathlib import Path
from typing import Optional, Callable, Awaitable

import connexion
import aiohttp
from aiohttp import web
from aiohttp.web import Request
from aiohttp.web_exceptions import HTTPPermanentRedirect
from aiohttp.abc import AbstractRouter, StreamResponse
import aiohttp_cors

import gino
from aiohttp.web_middlewares import middleware

from .data_types import BaseType
from .connexion_utils import load_api_spec, AppResolver
from .config import Config
from flask import g, has_request_context


db = gino.Gino()
__version__ = "1.0.0"

async def swaggr_ui_redirect(request):
    prefix = request.app["config"].SCRIPT_NAME
    location = f"{prefix or ''}/ui/"
    raise HTTPPermanentRedirect(location=location)


@middleware
async def compression_middleware(request: Request, handler: Callable[[Request], Awaitable[StreamResponse]]):
    """Enables compression on JSON responses"""
    response = await handler(request)
    if response.content_type == "application/json":
        response.enable_compression()
    return response


@middleware
async def set_schema(request: Request, handler: Callable[[Request], Awaitable[StreamResponse]]):
    schema = request.headers.get("TENANT")
    response = await handler(request)
    return response


def create_app(test_db_uri: Optional[str] = None):
    app = connexion.AioHttpApp(__name__, port=5000, specification_dir="", only_one_api=True)
    config = Config()

    spec_path = Path(__file__).parent / "api-spec.yaml"
    spec, operation_parameters = load_api_spec(spec_path, version=__version__, components=[BaseType])
    if config.SCRIPT_NAME:
        spec["servers"] = [{"url": config.SCRIPT_NAME}]
    
    app.add_api(
        spec,
        options={"swagger_ui": True, "middlewares": [compression_middleware, set_schema,]},
        resolver=AppResolver(operation_parameters),
        pass_context_arg_name="request",
    )

    aiohttp_app: aiohttp.web.Application = app.app
    aiohttp_app._client_max_size = config.MAX_REQUEST_SIZE
    aiohttp_app.add_routes([web.get("/", swaggr_ui_redirect)])
    aiohttp_app["HTTPS"] = config.HTTPS
    aiohttp_app["config"] = config
    # register_login_handlers(aiohttp_app, config.AUTH_SERVICE_URL)

    cors_options = aiohttp_cors.ResourceOptions(
        allow_credentials=True, expose_headers="*", allow_headers="*", allow_methods=["DELETE", "GET", "PATCH", "POST"]
    )
    origins = ["http://localhost:8080"]
    cors = aiohttp_cors.setup(app.app, defaults={origin: cors_options for origin in origins})

    for route in app.app.router.routes():
        cors.add(route)

    if config.SCRIPT_NAME:
        app.app._router = RouterSubpathMiddleware(app.app.router, config.SCRIPT_NAME or "")

    
    async def on_startup(app: web.Application):
        if test_db_uri:
            uri = test_db_uri
        else:
            uri = config.SQLALCHEMY_DATABASE_URI
        app["engine"] = await gino.create_engine(uri)
        from .models import db

        db.bind = app["engine"]

    aiohttp_app.on_startup.append(on_startup)

    return app


class RouterSubpathMiddleware:
    """Wrapper for a Router to support hosting on a subpath"""

    def __init__(self, router: AbstractRouter, subpath="/"):
        self._router = router
        if not subpath[-1] == "/":
            subpath += "/"
        self._subpath = subpath

    def __getattr__(self, key):
        return getattr(self._router, key)

    async def resolve(self, request: Request):
        if request.url.path.startswith(self._subpath):
            url = request.url.with_path(request.url.path[len(self._subpath) :])
            request = request.clone(rel_url=url)
        return await self._router.resolve(request)
