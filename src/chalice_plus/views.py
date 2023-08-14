from functools import cache, cached_property
from chalice import Response
from chalice.app import BadRequestError, ForbiddenError, MethodNotAllowedError, NotFoundError
from marshmallow.exceptions import ValidationError
from sqlalchemy.orm import Session
from chalice_plus.exceptions import InvalidRouteParameter
from chalice_plus.masking import Mask, mask_schema


class APIView:
    allowed_methods = ("get", "post", "put", "patch", "delete")
    schema_class = None
    authenticator_class = None
    permission_classes = {}
    mask_header = "x-fields"

    @classmethod
    def as_view(cls, name=""):
        def view(*args, **kwargs):
            self = cls()
            return self.dispatch(view, *args, **kwargs)
        view.allowed_methods = cls.allowed_methods
        view.permission_classes = cls.permission_classes
        return view

    @cache
    def get_schema(self, many=False):
        assert self.schema_class is not None, (
            "'%s' should either include a `schema_class` attribute, "
            "or override the `get_schema_class()` method."
            % self.__class__.__name__
        )
        return self.schema_class(many=many)

    @cache
    def get_load_schema(self, many=False):
        return self.get_schema(many=many)

    @cache
    def get_dump_schema(self, many=False):
        schema = self.get_schema(many=many)
        if self.mask:
            schema = mask_schema(schema, self.mask)
        return schema

    def dispatch(self, view, *args, **kwargs):
        self.request = view.app.current_request
        with Session(view.app.engine) as session:
            self.session = session

            method = self.request.method.lower()
            if method in self.allowed_methods:
                self.clean_url_parameters(view, **kwargs)
                self.check_permissions(method)
                return getattr(self, method)(self.request, *args, **kwargs)

        raise MethodNotAllowedError(f"Unsupported method: {method}")

    def clean_url_parameters(self, view, **kwargs):
        for parameter, converter in view.parameter_converters.items():
            try:
                kwargs[parameter] = converter(kwargs.get(parameter))
            except InvalidRouteParameter:
                raise NotFoundError

        self.kwargs = kwargs

    def check_permissions(self, method):
        if self.authenticator_class:
            permission_classes = self.permission_classes.get(method, [])
            for permission_class in permission_classes:
                permission = permission_class()
                if not permission.has_permission(self):
                    raise ForbiddenError(getattr(permission, 'message'))

    @cached_property
    def authenticator(self):
        if self.authenticator_class:
            return self.authenticator_class(self.request, self.session)

    @cached_property
    def mask(self):
        return self.get_mask()

    def get_mask(self):
        mask_string = self.request.headers.get(self.mask_header)
        if mask_string:
            return Mask(mask_string)


class SingleObjectMixin:
    pk_url_kwarg = 'id'

    def get_object(self):
        if self.pk:
            return self.session.get(self.model, self.pk)

    @cached_property
    def pk(self):
        return self.kwargs.get(self.pk_url_kwarg)

    @cached_property
    def object(self):
        return self.get_object()

    def check_object_exists(self):
        if not self.object:
            raise NotFoundError(f"Object with {self.pk_url_kwarg} of {self.pk} not found.")


class RetrieveMixin:
    def get(self, request, *args, **kwargs):
        self.check_object_exists()
        schema = self.get_dump_schema()
        return schema.dump(self.object)


class ListMixin:
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        schema = self.get_dump_schema(many=True)
        return schema.dump(queryset.all())

    def get_queryset(self):
        return self.session.query(self.model)


class CreateMixin:
    def get_request_data(self):
        return self.request.json_body or {}

    def load_object(self, instance=None, partial=True):
        schema = self.get_load_schema()
        try:
            return schema.load(
                self.get_request_data(),
                session=self.session,
                instance=instance,
                partial=partial,
            )
        except ValidationError as e:
            raise BadRequestError(e.messages)

    def create_object(self):
        instance = self.load_object(partial=False)
        self.session.add(instance)
        self.session.commit()
        return instance

    def post(self, request, *args, **kwargs):
        instance = self.create_object()
        schema = self.get_dump_schema()
        return Response(body=schema.dump(instance), status_code=201)


class UpdateMixin:
    def get_request_data(self):
        data = self.request.json_body or {}
        if not self.object:
            data["id"] = self.pk
        return data

    def load_object(self, instance=None, partial=True):
        schema = self.get_load_schema()
        try:
            return schema.load(
                self.get_request_data(),
                session=self.session,
                instance=instance,
                partial=partial,
            )
        except ValidationError as e:
            raise BadRequestError(e.messages)

    def update_object(self, partial=True):
        instance = self.load_object(instance=self.object, partial=partial)
        self.session.add(instance)
        self.session.commit()
        return instance

    def patch(self, request, *args, **kwargs):
        self.check_object_exists()
        instance = self.update_object(partial=True)
        schema = self.get_dump_schema()
        return schema.dump(instance)

    def put(self, request, *args, **kwargs):
        instance = self.update_object(partial=False)
        schema = self.get_dump_schema()
        if self.object:
            return schema.dump(instance)
        return Response(body=schema.dump(instance), status_code=201)


class DeleteMixin:
    def delete(self, request, *args, **kwargs):
        self.check_object_exists()
        self.session.delete(self.object)
        self.session.commit()
        return Response(body="", status_code=204)


class RetrieveView(SingleObjectMixin, RetrieveMixin, APIView):
    allowed_methods = ("get", )


class UpdateView(SingleObjectMixin, UpdateMixin, APIView):
    allowed_methods = ("patch", )


class DeleteView(SingleObjectMixin, DeleteMixin, APIView):
    allowed_methods = ("delete", )


class RetrieveUpdateView(SingleObjectMixin, RetrieveMixin, UpdateMixin, APIView):
    allowed_methods = ("get", "patch")


class RetrieveDeleteView(SingleObjectMixin, RetrieveMixin, DeleteMixin, APIView):
    allowed_methods = ("get", "delete")


class UpdateDeleteView(SingleObjectMixin, DeleteMixin, UpdateMixin, APIView):
    allowed_methods = ("patch", "delete")


class RetrieveUpdateDeleteView(SingleObjectMixin, RetrieveMixin, DeleteMixin, UpdateMixin, APIView):
    allowed_methods = ("get", "patch", "delete")


class ListView(ListMixin, APIView):
    allowed_methods = ("get", )


class CreateView(CreateMixin, APIView):
    allowed_methods = ("post", )


class CreateListView(CreateMixin, ListMixin, APIView):
    allowed_methods = ("get", "post")
