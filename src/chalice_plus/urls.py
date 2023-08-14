import re
from functools import cached_property
from uuid import UUID

from chalice_plus.exceptions import InvalidRouteParameter, InvalidURLConfiguration


def register_url(app, route, view, authorizer=None, **kwargs):
    view.app = app
    r = Route(route)
    view.parameter_converters = r.parameter_converters

    for method in view.allowed_methods:
        permission_classes = view.permission_classes.get(method.lower())
        if permission_classes:
            app.route(r.path, methods=[method.upper()], authorizer=authorizer, **kwargs)(view)
        else:
            app.route(r.path, methods=[method.upper()], **kwargs)(view)


def register_urls(app, urls, **kwargs):
    for route, view in urls:
        register_url(app, route, view, **kwargs)


class Route:
    _parameters = None
    _path = None
    url_regex = re.compile(r"{(?:(?P<converter>[^>:]+):)?(?P<parameter>[^>]+)}")

    def __init__(self, route):
        self.route = route

    @cached_property
    def path(self):
        if self._path is None:
            self.parse_route()
        return self._path

    @cached_property
    def parameter_converters(self):
        if self._parameters is None:
            self.parse_route()
        return self._parameters

    def parse_route(self):
        route = self.route
        parts = []
        self._parameters = {}

        while True:
            match = self.url_regex.search(route)
            if not match:
                parts.append(route)
                break
            start = re.escape(route[: match.start()])
            parts.append(start)
            route = route[match.end():]
            parameter = match["parameter"]
            raw_converter = match["converter"]
            if raw_converter is None:
                raw_converter = "str"

            try:
                converter = get_converter(raw_converter)
            except KeyError:
                raise InvalidURLConfiguration(
                    f"URL route {self.route} uses invalid converter {raw_converter}."
                )
            parts.append(f"{{{parameter}}}")
            self._parameters[parameter] = converter

        self._path = "".join(parts)


def convert_to_int(value):
    try:
        return int(value)
    except ValueError:
        raise InvalidRouteParameter(value)


def convert_to_uuid(value):
    try:
        uuid_obj = UUID(value)
    except ValueError:
        raise InvalidRouteParameter(value)
    if str(uuid_obj) == value:
        return value
    raise InvalidRouteParameter(value)


def get_converter(parameter_type):
    return {
        "int": convert_to_int,
        "str": str,
        "uuid": convert_to_uuid,
    }[parameter_type]
