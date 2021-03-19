from .connexion_utils import _mk_response
from connexion import problem
from http import HTTPStatus
from app.models import TestModel
from aiohttp import web
from functools import wraps
# from sqlalchemy.schema import Sc
from . import db

from tenent.tenant import check_tenant

@check_tenant(db=db)
async def healthz_live(request: web.Request):
    data = await db.all(TestModel.query)
    return _mk_response({"success": True}, HTTPStatus.OK)


async def healthz_ready(request):
    # The ready endpoint should return success if the application is ready to serve requests. If this check fails then
    # no traffic will be routed to the pod.
    if not await is_ready(request):
        return problem(HTTPStatus.SERVICE_UNAVAILABLE, "Service unavailable", "Application is not ready")
    return _mk_response({"success": True}, HTTPStatus.OK)