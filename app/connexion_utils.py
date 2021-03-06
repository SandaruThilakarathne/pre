import importlib
from enum import Enum
from pathlib import Path
from typing import Tuple, Dict, List, Optional, Any, TypeVar, Type, Union, Mapping
from inspect import signature, Parameter
from werkzeug.local import LocalProxy
from flask import g, has_request_context

import yaml
from connexion import Resolver
from connexion.lifecycle import ConnexionResponse

from dataclasses_jsonschema import JsonSchemaMixin, SchemaType

from .data_types import JsonDict

T = TypeVar("T", bound=JsonSchemaMixin)


def has_var_args(parameters: Mapping[str, Parameter]) -> bool:
    argument_types = {param.kind for param in parameters.values()}
    return Parameter.VAR_KEYWORD in argument_types or Parameter.VAR_POSITIONAL in argument_types


def get_enum_from_path(import_path: str) -> Type[Enum]:
    module_path, enum_name = import_path.rsplit(".", maxsplit=1)
    module = importlib.import_module(module_path)
    enum_type = getattr(module, enum_name)
    assert issubclass(enum_type, Enum)
    return enum_type


def load_api_spec(
    path: Union[str, Path], version: str, components: Optional[List[Type[T]]] = None
) -> Tuple[JsonDict, Dict[str, List[str]]]:
    """Loads the API spec YAML and adds the schema definitions"""

    def _read_parameters(parameters: List) -> List[str]:
        param_names = []
        for param in parameters:
            if "$ref" in param:
                param_names.append(global_params[param["$ref"].split("/")[-1]]["name"])
            else:
                param_names.append(param["name"])
            # Set any enum values
            if "x-enum-name" in param.get("schema", {}) and len(param["schema"].get("enum", [])) == 0:
                param["schema"]["enum"] = [
                    member.value for member in get_enum_from_path("app.data_types." + param["schema"]["x-enum-name"])
                ]
        return param_names

    with open(path, "r") as spec_file:
        spec = yaml.safe_load(spec_file)
        for component in components or []:
            spec["components"]["schemas"].update(component.all_json_schemas(schema_type=SchemaType.SWAGGER_V3))
        spec["info"]["version"] = version
        global_params = spec["components"].get("parameters", [])
        operation_parameters = {}
        for path, path_data in spec["paths"].items():
            path_parameters: List[str] = []
            for method, operation_data in path_data.items():
                if method == "parameters":
                    path_parameters = _read_parameters(operation_data)
                elif "operationId" in operation_data:
                    operation_parameters[operation_data["operationId"]] = path_parameters + _read_parameters(
                        operation_data.get("parameters", [])
                    )
        return spec, operation_parameters


class AppResolver(Resolver):
    """Override `Resolver` to prefix operationId with the module name.

    This also checks that each handler function's arguments match the operation parameters

    **Note:** This can be done with the `x-swagger-router-controller` property but it
    doesn't seem like this can be set globally for the whole api.
    """

    def __init__(self, operation_parameters: Dict[str, List[str]]) -> None:
        super().__init__()
        self.operation_parameters = operation_parameters

    def resolve_operation_id(self, operation):
        operation_id = super().resolve_operation_id(operation)
        handler_path = __package__ + ".api." + operation_id
        func = self.resolve_function_from_operation_id(handler_path)
        arguments = signature(func).parameters
        if not has_var_args(arguments):
            # Check that all of the parameter names match
            for parameter in self.operation_parameters[operation_id]:
                assert parameter in arguments, f"{parameter} not in {func.__name__} arguments"
        return handler_path


def _mk_response(content: Any, status: int):
    return ConnexionResponse(body=content, status_code=status)
