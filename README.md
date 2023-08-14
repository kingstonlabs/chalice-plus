# Chalice Plus
Chalice Plus is an opinionated serverless python framework for quickly building REST APIs based on SQLAlchemy models.

It is an extension for AWS Chalice that adds tools to speed up development and avoid boilerplate code.

Features include:
* [Class based views](#user-content-class-based-views)
* [SQLAlchemy and alembic integration](#user-content-alembic-integration)
* Marshmallow schema integration
* [Authentication](#user-content-authentication)
* [Permissions](#user-content-permissions)
* [Field masking](#user-content-field-masking)
* [URL parameter types](#user-content-urls)
* [SSM parameter support](#user-content-ssm-parameters)
* [Custom deploy commands](#user-content-chalice_plus-deploy)


## Compatibility
`chalice_plus` requires Python 3.9+


## Installation
You can install `chalice_plus` with pip:

```
$ pip install chalice_plus
```

Attach an engine to the app in `app.py`:
```
from sqlalchemy import create_engine
app = Chalice(app_name='books-api')
app.engine = create_engine(f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}/{DATABASE_NAME}")
```


## Overview
API endpoints can be created quickly and easily using class-based views - see the example below.

Note: Application code is stored in the `chalicelib` folder per `chalice` conventions.

`app.py`:
```
from chalicelib.urls import urlpatterns

register_urls(app, urlpatterns)
```

`chalicelib/urls.py`:
```
urlpatterns = [
    ("/books", BookListView.as_view()),
    ("/books/{uuid:id}", BookDetailView.as_view()),
]
```

`chalicelib/apps/books/views.py`:
```
from chalice_plus.views import RetrieveUpdateDeleteView, CreateListView

class BookDetailView(RetrieveUpdateDeleteView):
    model = Book
    schema_class = BookSchema

class BookListView(CreateListView):
    model = Book
    schema_class = BookSchema
```

`chalicelib/apps/books/models.py`:
```
class Book(Base):
    __tablename__ = "books"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    title = Column(String, nullable=False)
    description = Column(Text(), nullable=False)
```

`chalicelib/apps/books/schemas.py`:
```
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

class BookSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Book
        include_relationships = True
        load_instance = True
```

## Example Project
To see how everything fits together, please see the
[example project](https://github.com/kingstonlabs/chalice_plus_example).


## Class Based Views
Views can inherit from pre-defined `chalice_plus` views:

* RetrieveView
* UpdateView
* DeleteView
* RetrieveUpdateView
* RetrieveDeleteView
* UpdateDeleteView
* RetrieveUpdateDeleteView
* ListView
* CreateView
* CreateListView

Alternatively a custom view can be created using the generic `APIView` and defining custom methods and attributes.

The current request is available using `self.request` and the current database session is available using `self.session`. Any url kwargs can also be accessed in `self.kwargs`.

By default, the retrieve, update and delete views fetch an object based on the id in the url, but custom behaviour can also be defined.

To use a different url id, define `pk_url_kwarg`:
```
urlpatterns = [
    ("/books/{uuid:my_book_id}", BookDetailView.as_view()),
]

class BookDetailView(RetrieveUpdateDeleteView):
    model = Book
    schema_class = BookSchema
    pk_url_kwarg = "my_book_id"
```

To override the fetch behaviour, define `get_object`:

```
class BookDetailView(RetrieveUpdateDeleteView):
    model = Book
    schema_class = BookSchema

    def get_object(self):
        return self.session.query(Book).filter_by(
            published=True,
            id=self.pk,
        ).first()
```

Or to completely define the behaviour, override the http method:
```
class BookDetailView(RetrieveUpdateDeleteView):
    model = Book
    schema_class = BookSchema

    def get(self, request, *args, **kwargs):
        return {"custom": "data"}
```

For list views the queryset can be overridden:
```
class BookListView(ListView):
    model = Book
    schema_class = BookSchema

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter_by(published=True)
        return queryset
```

For update and create views, the request data an be intercepted:
```
class BookCreateView(CreateView):
    model = Book
    schema_class = BookSchema

    def get_request_data(self):
        data = super().get_request_data()
        data['intercepted'] = True
        return data
```

The model can also be intercepted before saving by overriding `load_object` - this can be useful when assigning `created_by` or `updated_by` fields:
```
class BookCreateView(CreateView):
    model = Book
    schema_class = BookSchema
    permission_classes = {"post": [IsAuthenticated]}
    authenticator_class = MyAuthenticator

    def load_object(self, *args, **kwargs):
        obj = super().load_object(*args, **kwargs)
        obj.created_by = self.authenticator.user
        return obj
```

To restrict which http methods are allowed on a view, `allowed_methods` can be set:
```
class BookListView(APIView):
    allowed_methods = ("post", "get")
```

When inheriting from a `chalice_plus` view, `allowed_methods` will already be set appropriately, but can be overridden.

For example, by default `put` requests are not allowed (use `patch` for partial updates). To enable `put` on an `UpdateView`:

```
class BookUpdateView(UpdateView):
    model = Book
    schema_class = BookSchema
    allowed_methods = ("patch", "put")
```

## URLs
URLs can be defined as follows:
```
urlpatterns = [
    ("/authors", AuthorListView.as_view()),
    ("/authors/{uuid:id}", AuthorDetailView.as_view()),
    ("/books", BookListView.as_view()),
    ("/books/{uuid:id}", BookDetailView.as_view()),
]
```

Then registered in `app.py`:

```
from chalice_plus.urls import register_urls
from chalicelib.urls import urlpatterns

register_urls(app, urlpatterns)
```

Note that in the above example, a parameter type of `uuid` has been defined. This is optional, but useful to validate input. The following types are available:
* `uuid` - validates as a UUID. The parameter value is available in `self.kwargs` as a string.
* `int` - validates as an integer. The parameter value is available in `self.kwargs` as an integer.
* `str` - validates as a string. The parameter value is available in `self.kwargs` as a string.


## Authorization

An authorizer can be passed to `register_urls`. The authorizer will then be used to authorize any views which define [permissions](#user-content-permissions).
If a view does not define permissions for an http method, no authorization will be applied.

`app.py`
```
from chalice_plus.urls import register_urls

authorizer = CognitoUserPoolAuthorizer(COGNITO_USER_POOL_NAME, provider_arns=[COGNITO_USER_POOL_ARN])
register_urls(app, urlpatterns, cors=cors_config, authorizer=authorizer)
```

## Authentication
Views can also define an authenticator class. The authenticator is used to get the current user: `self.authenticator.user` or `self.authenticator.user_id`.

`chalice_plus` comes with a `CognitoAuthenticator`, however the `get_user` function needs to be defined manually. For example:

`chalicelib/apps/users/authenticators.py`
```
import os
from chalice_plus.authenticators import CognitoAuthenticator
from chalicelib.apps.users.models import User

class CustomCognitoAuthenticator(CognitoAuthenticator):
    def get_user(self):
        if self.user_id:
            return self.session.get(User, self.user_id)

    def get_user_id(self):
        if "AWS_CHALICE_CLI_MODE" in os.environ:
            return "069522e8-a001-70a7-616e-1273a47f3f02"
        return super().get_user_id()
```

`chalicelib/apps/books/views.py`
```
class BookDetailView(RetrieveUpdateDeleteView):
    model = Book
    schema_class = BookSchema
    authenticator_class = CustomCognitoAuthenticator
```


## Permissions
Views can be restricted by permission and will generally require an authenticator.

`chalice_plus` comes with a few default permission classes:
* `IsAuthenticated`
* `IsAdmin`
* `IsOwner`
* `IsOwnerOrAdmin`

The owner is checked by looking at `object.created_by` and admin is checked by looking at `user.is_superuser`.

If these assumptions do not apply, custom permission classes can be written:

```
class IsStaff:
    message = "User is not staff"

    def has_permission(self, view):
        user = view.authenticator.user
        return user and user.is_staff
```

Permissions are applied as a list on a per http-method basis. All permissions in the list need to pass, otherwise a 403 forbidden response will be issued:

```
class BookDetailView(RetrieveUpdateDeleteView):
    model = Book
    schema_class = BookSchema
    authenticator_class = CustomCognitoAuthenticator
    permission_classes = {
        "get": [IsAuthenticated]
        "delete": [IsOwnerOrAdmin],
        "patch": [IsOwnerOrAdmin],
    }
```

If no permission is specified for a method (and it is in `allowed_methods`), it is openly available without authorization.


## Field masking

`chalice_plus` supports partial object fetching by supplying a custom header in the request.

By default the header is `X-Fields` but it can be changed by setting the view's `mask_header` attribute.

For example, to only fetch the `id` and `title` of books, we can use the `{id,title}` mask:
```
$ curl 127.0.0.1:8000/books -H "X-Fields: {id,title}"
[{"id":"f235adde-69a3-468f-b008-d22cd576dd98","title":"The Very Hungry Caterpillar"},{"id":"10e417a6-2cb4-4a03-8679-63491c0d17b9","title":"The Shining"}]
```

It is also possible to span relationships using the field mask:
```
$ curl 127.0.0.1:8000/books -H "X-Fields: {id,title,author{name}}"
[{"id":"f235adde-69a3-468f-b008-d22cd576dd98","title":"The Very Hungry Caterpillar", "author": {"name": "Eric Carle"}},{"id":"10e417a6-2cb4-4a03-8679-63491c0d17b9","title":"The Shining", "author": {"name": "Stephen King"}}]
```

Note that in this case separate queries are performed to fetch the author for each book. This can be optimised by joining the authors table in the view:

```
class BookListView(ListView):
    model = Book
    schema_class = BookSchema

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.mask and "author" in self.mask:
            queryset = queryset.options(joinedload(Book.author))
        return queryset
```

To allow the `X-Fields` header, a `CORSConfig` needs to be defined in `app.py`:

```
from chalice import Chalice, CORSConfig

cors_config = CORSConfig(allow_headers=['X-Fields'])
register_urls(app, urlpatterns, cors=cors_config)
```


## Alembic integration
Create an alembic folder at the same level as `app.py`:

`$ alembic init alembic`

In `alembic.ini`, ensure `sqlalchemy.url` is set to blank:

`sqlalchemy.url = `

This helps us dynamically set the value in `alembic/env.py`:

```
if not config.get_main_option("sqlalchemy.url"):
    connection_string = f"postgresql+psycopg2://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}/{settings.DATABASE_NAME}"
    config.set_main_option("sqlalchemy.url", connection_string)
```

Note that the deploy command below sets `sqlalchemy.url` to the remote database during deploy. It is important that `sqlalchemy.url` doesn't get overwritten in `env.py` if it has already been set externally.

All models  should be registered in `env.py`:
```
from chalicelib.models import Base
from chalicelib.apps.books.models import Author, Book
from chalicelib.apps.users.models import User
target_metadata = [Base.metadata]
```


## `chalice_plus deploy`
`chalice_plus` includes a deploy command which will migrate the remote database before deploy, reverting if the deploy fails:

```
$ chalice_plus deploy
```

To connect to the remote database, credentials will be fetched from SSM.

At a minimum, the following need to be set in SSM:
* `{app_name}.{stage}.DATABASE_USER`
* `{app_name}.{stage}.DATABASE_PASSWORD`
* `{app_name}.{stage}.DATABASE_HOST`
* `{app_name}.{stage}.DATABASE_NAME`


## SSM Parameters
It can be useful to store secret variables as SSM parameters, `chalice_plus` can fetch these during a deploy and save as environment variables within the lambda.

In `.chalice/config.json`, set the parameter names using `"ssm_parameters"`:
```
{
  "version": "2.0",
  "app_name": "book-api",
  "automatic_layer": true,
  "ssm_parameters": [
    "DATABASE_USER",
    "DATABASE_PASSWORD",
    "DATABASE_HOST",
    "DATABASE_NAME"
  ],
  ...
}
```

Any SSM parameters must have a name in the following format:
`{app_name}.{stage}.{parameter_name}`

It's also possible to skip alembic migrations - the following just deploys as usual, but with SSM parameter support:
```
$ chalice_plus deploy --skip-migration
```

## Filtering, sorting & pagination
Not currently supported, but coming soon.
