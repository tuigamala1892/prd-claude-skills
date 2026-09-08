# Task summary

**10 tasks** — 0-setup 3, 1-foundation 3, 2-backend 3, 4-integration 1

Derived from the task files by `build-manifest.py`. Do not edit: it is rewritten whenever the manifest is, and `--verify` fails when it has drifted.

| Task | Layer | From | Tier | Criteria | Objective | Files |
|---|---|---|---|---|---|---|
| `L0-001` | 0-setup | — | — | — | Create the three root-level project files for Link Shelf: a pyproject.toml declaring the project metadata and its fou... | `pyproject.toml`<br>`requirements.txt`<br>`.gitignore` |
| `L0-002` | 0-setup | — | — | — | Create the `app` and `app.models` Python packages and a pytest.ini that sets the test path to `tests` and puts the re... | `pytest.ini`<br>`app/__init__.py`<br>`app/models/__init__.py` |
| `L0-003` | 0-setup | — | — | — | Create the SQLite database plumbing (engine, session factory, declarative Base, get_db dependency), a bare FastAPI ap... | `app/database.py`<br>`app/main.py`<br>`tests/conftest.py`<br>`tests/test_setup.py` |
| `L1-001` | 1-foundation | save-link | must-have | — | Declare the `Link` SQLAlchemy model - the table that stores one saved URL with an optional title and the time it was... | `app/models/link.py`<br>`app/models/__init__.py`<br>`tests/test_model_link.py` |
| `L1-002` | 1-foundation | tag-links | should-have | — | Declare the `Tag` SQLAlchemy model - the table holding one free-text tag name, unique across the shelf and compared c... | `app/models/tag.py`<br>`app/models/__init__.py`<br>`tests/test_model_tag.py` |
| `L1-003` | 1-foundation | tag-links | should-have | — | Declare the `LinkTag` join table - one row per attachment of one tag to one link, with a composite primary key over (... | `app/models/link_tag.py`<br>`app/models/link.py`<br>`app/models/__init__.py`<br>`tests/test_model_link_tag.py` |
| `L2-001` | 2-backend | save-link | must-have | 1, 2, 3, 4 | Create the Pydantic request and response schemas for a link and the `POST /links` route that stores one, so that post... | `app/api/__init__.py`<br>`app/schemas/link.py`<br>`app/api/save_link.py`<br>`tests/test_save_link.py` |
| `L2-002` | 2-backend | list-links<br>tag-links | must-have | 1, 2, 3, 4<br>3 | Create the `GET /links` route: it returns every stored link as a JSON array ordered most recently created first, an e... | `app/api/list_links.py`<br>`tests/test_list_links.py` |
| `L2-003` | 2-backend | tag-links | should-have | 1, 2, 4 | Create the tag request schema and the `POST /links/{link_id}/tags` route: posting a list of tag names to an existing... | `app/schemas/tag.py`<br>`app/api/tag_links.py`<br>`tests/test_tag_links.py` |
| `L4-001` | 4-integration | save-link<br>list-links<br>tag-links | must-have | —<br>—<br>— | Mount the three existing routers - `save_link`, `list_links` and `tag_links` - on the existing FastAPI application in... | `app/main.py`<br>`tests/test_integration.py` |
