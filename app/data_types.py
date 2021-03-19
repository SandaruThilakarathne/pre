from dataclasses_jsonschema import JsonSchemaMixin
from typing import Dict, Any, List, Optional

JsonDict = Dict[str, Any]

class BaseType(JsonSchemaMixin):
    pass