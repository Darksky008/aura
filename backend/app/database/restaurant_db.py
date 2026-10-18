import logging
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.core.config import get_settings

log = logging.getLogger("database.restaurant")


class RestaurantBase(DeclarativeBase):
    pass


class MenuItem(RestaurantBase):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dish_name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)


def resolve_restaurant_db_path(custom_path: str | Path | None = None) -> Path:
    """Resolve the path to aura_restaurant.db using a reliable project-relative strategy."""
    path_str = str(custom_path or get_settings().restaurant_database_path or "database/aura_restaurant.db")
    candidate = Path(path_str)

    # 1. Absolute path check
    if candidate.is_absolute() and candidate.exists():
        return candidate

    # 2. Project relative to backend root: backend/app/database -> backend
    backend_root = Path(__file__).resolve().parent.parent.parent
    if (backend_root / candidate).exists():
        return (backend_root / candidate).resolve()

    # If candidate has "database/...", check backend / candidate
    if (backend_root / "database" / candidate.name).exists():
        return (backend_root / "database" / candidate.name).resolve()

    # 3. Check relative to CWD
    cwd = Path.cwd()
    if (cwd / candidate).exists():
        return (cwd / candidate).resolve()
    if (cwd / "backend" / candidate).exists():
        return (cwd / "backend" / candidate).resolve()
    if (cwd / "backend" / "database" / candidate.name).exists():
        return (cwd / "backend" / "database" / candidate.name).resolve()

    # Fallback to backend_root / database / aura_restaurant.db
    return (backend_root / "database" / "aura_restaurant.db").resolve()


@lru_cache(maxsize=4)
def get_restaurant_engine(db_path: str | Path | None = None):
    resolved = resolve_restaurant_db_path(db_path)
    url = f"sqlite:///{resolved.as_posix()}"
    log.info("Connecting to restaurant database: %s", url)
    return create_engine(url, connect_args={"check_same_thread": False})


@lru_cache(maxsize=4)
def get_restaurant_session_maker(db_path: str | Path | None = None):
    engine = get_restaurant_engine(db_path)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_restaurant_db(db_path: str | Path | None = None) -> Iterator[Session]:
    sm = get_restaurant_session_maker(db_path)
    session = sm()
    try:
        yield session
    finally:
        session.close()
