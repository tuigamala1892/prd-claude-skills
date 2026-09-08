# Task summary — link-shelf

**14 tasks** — 0-setup 4, 3-backend 6, 4-foundation 4

Derived from the task files by `build-manifest.py`. Do not edit: it is rewritten whenever the manifest is, and `--verify` fails when it has drifted.

| Task | Layer | From | Tier | Criteria | Objective | Files |
|---|---|---|---|---|---|---|
| `L0-001` | 0-setup | — | — | — | Create the two top-level Python packages (`app` for application code, `tests` for the test suite) and a `.gitignore`... | `.gitignore`<br>`app/__init__.py`<br>`tests/__init__.py` |
| `L0-002` | 0-setup | — | — | — | Create the three subpackages of `app` that layers 3 and 4 write into -- app.models, app.api and app.schemas -- each w... | `app/api/__init__.py`<br>`app/models/__init__.py`<br>`app/schemas/__init__.py` |
| `L0-003` | 0-setup | — | — | — | Write pyproject.toml declaring the project metadata, the four runtime dependencies (fastapi, sqlalchemy, pytest, http... | `pyproject.toml` |
| `L0-004` | 0-setup | — | — | — | Create a virtual environment at .venv, install the project and its four declared dependencies into it in editable mod... | — |
| `L3-001` | 3-backend | save-link | must-have | — | Define the two Pydantic v2 models that carry link payloads over HTTP: LinkCreate for the request body of POST /links,... | `app/schemas/link.py`<br>`tests/test_link_schemas.py` |
| `L3-002` | 3-backend | save-link | must-have | — | Create the FastAPI application object in app/main.py and an empty APIRouter in app/api/links.py, wire the router into... | `app/main.py`<br>`app/api/links.py`<br>`tests/test_app_smoke.py` |
| `L3-003` | 3-backend | save-link | must-have | 1, 2, 3, 4 | Add the POST /links route handler to app/api/links.py. It accepts a url and an optional title, stores one Link row, a... | `app/api/links.py`<br>`tests/test_save_link.py` |
| `L3-004` | 3-backend | list-links<br>tag-links | must-have | 1, 2, 3, 4<br>3 | Add a GET /links handler to app/api/links.py that returns every stored link as a JSON array ordered most recently cre... | `app/api/links.py`<br>`tests/test_list_links.py` |
| `L3-005` | 3-backend | tag-links | should-have | — | Create app/schemas/tag.py defining the Pydantic request model for attaching one or more free-text tag names to a link... | `app/schemas/tag.py`<br>`tests/test_tag_schemas.py` |
| `L3-006` | 3-backend | tag-links | should-have | 1, 2, 4 | Add a POST /links/{link_id}/tags handler to app/api/links.py that attaches one or more free-text tags to an existing... | `app/api/links.py`<br>`tests/test_tag_links.py` |
| `L4-001` | 4-foundation | save-link<br>list-links<br>tag-links | must-have | —<br>—<br>— | Create app/db.py: the SQLAlchemy 2.x declarative Base that every model in this project subclasses, a file-backed SQLi... | `app/db.py`<br>`tests/test_db.py` |
| `L4-002` | 4-foundation | save-link | must-have | 1, 2, 3 | Create the SQLAlchemy model `Link` in app/models/link.py - the entity save-link owns and the one every other feature... | `app/models/link.py`<br>`app/models/__init__.py`<br>`tests/test_link_model.py` |
| `L4-003` | 4-foundation | tag-links | should-have | 1, 2, 4 | Create the two models tag-links owns: `Tag` in app/models/tag.py and the `LinkTag` join table in app/models/link_tag.... | `app/models/tag.py`<br>`app/models/link_tag.py`<br>`app/models/__init__.py`<br>`tests/test_tag_models.py` |
| `L4-004` | 4-foundation | save-link<br>list-links<br>tag-links | must-have | —<br>—<br>— | Create tests/conftest.py providing two fixtures - `db_session`, a SQLAlchemy session against a fresh empty SQLite dat... | `tests/conftest.py`<br>`tests/test_fixtures.py` |
