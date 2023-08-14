import pytest

from chalice import Chalice, CognitoUserPoolAuthorizer
from chalice.test import Client
from chalice_plus.permissions import IsAdmin, IsAuthenticated, IsOwner, IsOwnerOrAdmin
from chalice_plus.urls import register_url
from chalice_plus.views import (
    CreateView, CreateListView, DeleteView, ListView, RetrieveView, UpdateView
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from tests.app.authenticators import CustomCognitoAuthenticator
from tests.app.models import Base, Author, Book, User
from tests.app.schemas import AuthorSchema, BookSchema


@pytest.fixture
def setup_db(session):
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def engine():
    return create_engine("sqlite://")


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def app(engine):
    app = Chalice(app_name="testclient")
    app.engine = engine
    return app


@pytest.fixture(autouse=True)
def create_db(engine):
    Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def populate_db(session, create_db):
    user1 = User(id=1, username="monkey", is_superuser=True)
    user2 = User(id=2, username="horse")
    session.add_all([user1, user2])
    author1 = Author(id=1, name="Eric Carle", description="Writer and illustrator", created_by_id=1)
    author2 = Author(id=2, name="Stephen King", description="King of Horror", created_by_id=2)
    session.add_all([author1, author2])
    book1 = Book(
        id=1,
        title="The Very Hungry Caterpillar",
        description="The story of a very hungry caterpillar",
        author_id=1,
        created_by_id=1,
    )
    book2 = Book(
        id=2,
        title="The Shining",
        description="Jack Torrance stays at the Overlook Hotel",
        author_id=2,
        created_by_id=2,
    )
    book3 = Book(id=3, title="Carrie", description="About a girl", author_id=2, created_by_id=1)
    session.add_all([book1, book2, book3])
    session.commit()


@pytest.fixture
def client(app):
    with Client(app) as test_client:
        yield test_client


@pytest.fixture
def authorizer(app):
    return CognitoUserPoolAuthorizer("test_user_pool", provider_arns=["arn:1"])


@pytest.fixture
def book_detail_view(app):
    class BookDetailView(RetrieveView):
        model = Book
        schema_class = BookSchema

    register_url(app, "books/{int:id}", BookDetailView.as_view())


@pytest.fixture
def book_list_view(app):
    class BookListView(ListView):
        model = Book
        schema_class = BookSchema

    register_url(app, "books", BookListView.as_view())


@pytest.fixture
def book_create_view(app):
    class BookCreateView(CreateView):
        model = Book
        schema_class = BookSchema

        def load_object(self, *args, **kwargs):
            obj = super().load_object(*args, **kwargs)
            obj.created_by_id = 1
            return obj

    register_url(app, "books", BookCreateView.as_view())


@pytest.fixture
def book_update_view(app):
    class BookUpdateView(UpdateView):
        model = Book
        schema_class = BookSchema
        allowed_methods = ("patch", "put")

        def load_object(self, *args, **kwargs):
            obj = super().load_object(*args, **kwargs)
            if self.request.method.lower() == "put":
                obj.created_by_id = 1
            return obj

    register_url(app, "books/{int:id}", BookUpdateView.as_view())


@pytest.fixture
def book_delete_view(app):
    class BookDeleteView(DeleteView):
        model = Book
        schema_class = BookSchema

    register_url(app, "books/{int:id}", BookDeleteView.as_view())


@pytest.fixture
def author_create_list_view_is_admin(app):
    class AuthorCreateListView(CreateListView):
        model = Author
        schema_class = AuthorSchema
        authenticator_class = CustomCognitoAuthenticator
        permission_classes = {"post": [IsAdmin]}

        def load_object(self, *args, **kwargs):
            obj = super().load_object(*args, **kwargs)
            obj.created_by = self.authenticator.user
            return obj

    register_url(app, "authors", AuthorCreateListView.as_view())


@pytest.fixture
def author_detail_view_is_authenticated(app, authorizer):
    class AuthorDetailView(RetrieveView):
        model = Author
        schema_class = AuthorSchema
        authenticator_class = CustomCognitoAuthenticator
        permission_classes = {"get": [IsAuthenticated]}

    register_url(app, "authors/{int:id}", AuthorDetailView.as_view(), authorizer=authorizer)


@pytest.fixture
def book_create_view_is_admin(app):
    class BookCreateView(CreateView):
        model = Book
        schema_class = BookSchema
        authenticator_class = CustomCognitoAuthenticator
        permission_classes = {"post": [IsAdmin]}

        def load_object(self, *args, **kwargs):
            obj = super().load_object(*args, **kwargs)
            obj.created_by = self.authenticator.user
            return obj

    register_url(app, "books", BookCreateView.as_view())


@pytest.fixture
def book_update_view_is_owner(app):
    class BookUpdateView(UpdateView):
        model = Book
        schema_class = BookSchema
        authenticator_class = CustomCognitoAuthenticator
        permission_classes = {"patch": [IsOwner]}

    register_url(app, "books/{int:id}", BookUpdateView.as_view())


@pytest.fixture
def book_update_view_is_owner_or_admin(app):
    class BookUpdateView(UpdateView):
        model = Book
        schema_class = BookSchema
        authenticator_class = CustomCognitoAuthenticator
        permission_classes = {"patch": [IsOwnerOrAdmin]}

    register_url(app, "books/{int:id}", BookUpdateView.as_view())
