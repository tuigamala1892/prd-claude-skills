"""The brownfield codebase the CRD fixture starts from.

Kept as data rather than a checked-in tree so the whole app -- including the commit history
it is laid down in -- is reviewable in one place, and so `setup_crd_fixture.py` can assert
the result actually works before any run depends on it.

Design notes, in the spirit of §5.1's "choices that matter":

- **It works.** `pytest` passes on a fresh build. A brownfield fixture whose baseline is
  already broken cannot tell you whether a change request broke it.
- **It has history.** Five commits, not one. `/crd-investigate` may reasonably read git log,
  and a repository with a single "Initial commit" is not a brownfield project.
- **Deleting a link is destructive and tested.** The change request asks for archiving
  *without* removing delete, so the existing test is the thing that must survive.
- **Tags are a join table**, so a change touching links has to reason about `link_tags`
  rather than a column. Impact analysis on a string column would be trivial.
- **`app/api/__init__.py` re-exports the routers.** This was planted as a "shared file"
  trap on the assumption that a new endpoint must edit it. That assumption is wrong, and the
  first CRD run proved it: new routes go into the *existing* `links.py` router, which is
  already re-exported, so `__init__.py` correctly does not change. It is kept because it is
  realistic structure, not because it traps anything. A change needing a genuinely new
  router module would touch it.
- **No PROJECT.md.** Producing it is `/crd-context`'s job and the first thing to test.
"""

PYPROJECT = """\
[project]
name = "link-shelf"
version = "0.3.0"
description = "Save links, tag them, find them again."
requires-python = ">=3.11"
dependencies = ["fastapi", "sqlalchemy", "pydantic", "httpx", "uvicorn"]

[tool.pytest.ini_options]
testpaths = ["tests"]
"""

GITIGNORE = """\
__pycache__/
*.py[cod]
.venv/
*.db
.pytest_cache/
"""

README = """\
# Link Shelf

Save a link, tag it, find it again later.

    uvicorn app.main:app --reload

## Endpoints

| Method | Path                     | Purpose                        |
|--------|--------------------------|--------------------------------|
| POST   | /links                   | Save a link                    |
| GET    | /links                   | List links, optionally by tag  |
| DELETE | /links/{link_id}         | Delete a link permanently      |
| POST   | /links/{link_id}/tags    | Attach tags to a link          |
| GET    | /health                  | Liveness                       |

## Layout

    app/models/     SQLAlchemy models; tags are a join table, not a column
    app/api/        routers; app/api/__init__.py re-exports them
    tests/          pytest, SQLite in-memory
"""

DATABASE = '''\
"""Engine and session factory. SQLite so nothing external has to be running."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./link_shelf.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''

MODEL_LINK = '''\
"""A saved link."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.link_tag import link_tags


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    tags = relationship("Tag", secondary=link_tags, back_populates="links")
'''

MODEL_TAG = '''\
"""A tag. Many-to-many with Link through the link_tags join table."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.link_tag import link_tags


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    links = relationship("Link", secondary=link_tags, back_populates="tags")
'''

MODEL_LINK_TAG = '''\
"""The join table. Deliberately a table rather than a column on Link: a change that
touches links has to reason about the association, which is the interesting case."""

from sqlalchemy import Column, ForeignKey, Integer, Table

from app.database import Base

link_tags = Table(
    "link_tags",
    Base.metadata,
    Column("link_id", Integer, ForeignKey("links.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)
'''

MODELS_INIT = '''\
from app.models.link import Link
from app.models.link_tag import link_tags
from app.models.tag import Tag

__all__ = ["Link", "Tag", "link_tags"]
'''

SCHEMAS = '''\
"""Request and response shapes."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LinkCreate(BaseModel):
    url: str
    title: str = ""
    tags: list[str] = []


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class LinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    url: str
    title: str
    created_at: datetime
    tags: list[TagOut] = []


class TagsIn(BaseModel):
    tags: list[str]
'''

API_LINKS = '''\
"""Link endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Link, Tag
from app.schemas import LinkCreate, LinkOut, TagsIn

router = APIRouter(prefix="/links", tags=["links"])


def _tag(db: Session, name: str) -> Tag:
    tag = db.query(Tag).filter(Tag.name == name).first()
    if tag is None:
        tag = Tag(name=name)
        db.add(tag)
        db.flush()
    return tag


@router.post("", response_model=LinkOut, status_code=201)
def create_link(payload: LinkCreate, db: Session = Depends(get_db)) -> Link:
    if not payload.url.strip():
        raise HTTPException(status_code=422, detail="url must not be empty")
    link = Link(url=payload.url, title=payload.title)
    link.tags = [_tag(db, n) for n in payload.tags]
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.get("", response_model=list[LinkOut])
def list_links(tag: str | None = None, db: Session = Depends(get_db)) -> list[Link]:
    query = db.query(Link)
    if tag:
        query = query.join(Link.tags).filter(Tag.name == tag)
    return query.order_by(Link.created_at.desc()).all()


@router.delete("/{link_id}", status_code=204)
def delete_link(link_id: int, db: Session = Depends(get_db)) -> None:
    """Permanent. The change request asks for archiving *alongside* this, not instead of it."""
    link = db.get(Link, link_id)
    if link is None:
        raise HTTPException(status_code=404, detail="link not found")
    db.delete(link)
    db.commit()


@router.post("/{link_id}/tags", response_model=LinkOut)
def add_tags(link_id: int, payload: TagsIn, db: Session = Depends(get_db)) -> Link:
    link = db.get(Link, link_id)
    if link is None:
        raise HTTPException(status_code=404, detail="link not found")
    existing = {t.name for t in link.tags}
    for name in payload.tags:
        if name not in existing:
            link.tags.append(_tag(db, name))
    db.commit()
    db.refresh(link)
    return link
'''

API_HEALTH = '''\
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
'''

API_INIT = '''\
"""Router re-exports.

A shared file: anything adding an endpoint edits this, and two modules import from it.
"""

from app.api.health import router as health_router
from app.api.links import router as links_router

__all__ = ["health_router", "links_router"]
'''

MAIN = '''\
"""Application entry point."""

from fastapi import FastAPI

from app.api import health_router, links_router
from app.database import Base, engine
from app.models import Link, Tag, link_tags  # noqa: F401  (registers mappers)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Link Shelf", version="0.3.0")
app.include_router(health_router)
app.include_router(links_router)
'''

APP_INIT = '''\
__version__ = "0.3.0"
'''

CONFTEST = '''\
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
'''

TEST_LINKS = '''\
def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_list(client):
    r = client.post("/links", json={"url": "https://example.com", "title": "Example"})
    assert r.status_code == 201
    assert r.json()["url"] == "https://example.com"

    listed = client.get("/links").json()
    assert len(listed) == 1
    assert listed[0]["title"] == "Example"


def test_empty_url_rejected(client):
    assert client.post("/links", json={"url": "   "}).status_code == 422


def test_tags_and_filtering(client):
    client.post("/links", json={"url": "https://a.example", "tags": ["python"]})
    client.post("/links", json={"url": "https://b.example", "tags": ["rust"]})

    assert len(client.get("/links", params={"tag": "python"}).json()) == 1
    assert len(client.get("/links").json()) == 2


def test_add_tags_is_idempotent(client):
    link_id = client.post("/links", json={"url": "https://c.example"}).json()["id"]
    client.post(f"/links/{link_id}/tags", json={"tags": ["read-later"]})
    body = client.post(f"/links/{link_id}/tags", json={"tags": ["read-later"]}).json()
    assert [t["name"] for t in body["tags"]] == ["read-later"]


def test_delete_is_permanent(client):
    """The change request asks for archiving alongside delete, not instead of it.
    If a CRD-driven change makes this fail, it changed more than it was asked to."""
    link_id = client.post("/links", json={"url": "https://d.example"}).json()["id"]
    assert client.delete(f"/links/{link_id}").status_code == 204
    assert client.get("/links").json() == []
'''

TEST_MODELS = '''\
from app.models import Link, Tag


def test_tags_are_a_join_table_not_a_column():
    """Guards the shape the change request has to reason about."""
    assert not hasattr(Link, "tag_names")
    assert "tags" in Link.__mapper__.relationships
    assert "links" in Tag.__mapper__.relationships


def test_link_has_no_archive_flag_yet():
    """The starting state. A CRD run is expected to change this."""
    assert not hasattr(Link, "archived")
    assert not hasattr(Link, "archived_at")
'''

# (path, content, which commit it lands in) -- five commits, so the fixture has history.
FILES = [
    ("pyproject.toml", PYPROJECT, 0),
    (".gitignore", GITIGNORE, 0),
    ("README.md", README, 0),
    ("app/__init__.py", APP_INIT, 1),
    ("app/database.py", DATABASE, 1),
    ("app/models/link_tag.py", MODEL_LINK_TAG, 2),
    ("app/models/link.py", MODEL_LINK, 2),
    ("app/models/tag.py", MODEL_TAG, 2),
    ("app/models/__init__.py", MODELS_INIT, 2),
    ("app/schemas.py", SCHEMAS, 2),
    ("app/api/health.py", API_HEALTH, 3),
    ("app/api/links.py", API_LINKS, 3),
    ("app/api/__init__.py", API_INIT, 3),
    ("app/main.py", MAIN, 3),
    ("tests/conftest.py", CONFTEST, 4),
    ("tests/test_links.py", TEST_LINKS, 4),
    ("tests/test_models.py", TEST_MODELS, 4),
]

COMMITS = [
    "chore: project skeleton and dependencies",
    "feat: database engine and session factory",
    "feat: Link and Tag models with a link_tags join table",
    "feat: link and health endpoints",
    "test: cover create, list, tag filtering and delete",
]
