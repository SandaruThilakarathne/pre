from alembic import op
import sqlalchemy as sa
from app import db
from aiohttp import web_app
from functools import wraps
import requests


def get_non_system_schemas(exclude=[]):
    try:
        conn = op.get_bind()
        schemas = conn.execute(
            sa.text(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast', 'pg_temp_1', 'pg_toast_temp_1')"
            )
        ).fetchall()
        return [str(x[0]) for x in schemas if x not in exclude]
    except:
        return []


def schemas(exclude):
    try:
        conn = op.get_bind()
        schemas = conn.execute(
            sa.text("SELECT schema_name FROM information_schema.schemata")
        ).fetchall()
        return [ str(x[0]) for x in schemas if x not in exclude ]
    except:
        return []


def pre_schema(schemas=[], exclude=[]):
    print("here wer are")
    schemas = get_non_system_schemas() if len(schemas) == 0 else schemas
    print(schemas)
    def externel_wrapper(func):
        def wrapper(*args, **kwargs):
            for s in schemas:
                if s not in exclude:
                    print("Executing on schema {}".format(s))
                    try:
                        op.execute(sa.text("SET search_path TO {}".format(s)))
                        func(*args, **kwargs)
                        op.execute(sa.text("SET search_path TO default"))
                    except Exception as e:
                        op.execute(sa.text("SET search_path TO default"))
                        raise e
                else:
                    pass
        return wrapper
    return externel_wrapper

def get_schema(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        print(args)
        print(kwargs['request'].get("headers"))
    # with db.acquire():
    #     db.status("SET search_path TO myschema")
    return wrapper
