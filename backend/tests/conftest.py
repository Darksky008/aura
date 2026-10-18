import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ["RATE_LIMIT_PER_MINUTE"] = "100000"
os.environ["GROQ_API_KEY"] = ""
os.environ["ADMIN_API_KEY"] = ""
os.environ["APP_ENV"] = "development"
os.environ.setdefault("RESTAURANT_DATABASE_PATH", "")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db, make_engine
from app.main import app
from app.models import Hotel
from seed.run import seed_demo


@pytest.fixture()
def engine():
    eng = make_engine("sqlite://")
    eng.dispose()
    from sqlalchemy import create_engine
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    import app.models  # noqa: F401
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Session() as s:
        seed_demo(s)
        yield s


@pytest.fixture()
def hotel(db):
    return db.scalar(select(Hotel).where(Hotel.slug == "aurelia-grand"))


@pytest.fixture()
def restaurant(hotel):
    return hotel.restaurants[0]


@pytest.fixture()
def client(engine):
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Session() as s:
        seed_demo(s)

    def override():
        with Session() as s:
            yield s

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()
