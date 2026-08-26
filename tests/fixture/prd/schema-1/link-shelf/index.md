<prd>
  <meta>
    <name>Link Shelf</name>
    <slug>link-shelf</slug>
    <status>in-progress</status>
    <created>2026-08-10</created>
    <updated>2026-08-10</updated>
  </meta>

  <overview>
    <problem>
    People collect interesting links across chat, email and browser tabs, then lose
    them. There is no single place to drop a URL and find it again later.
    </problem>
    <users>
    A single developer using it locally. No authentication, no multi-tenancy, no
    sharing. This is deliberately the smallest useful shape of the idea.
    </users>
    <value-proposition>
    One endpoint to save a link, one to get them all back, and tags so the list stays
    navigable past a few dozen entries.
    </value-proposition>
  </overview>

  <tech-stack>
    <type>greenfield</type>
    <selected>
    Python 3.11, FastAPI 0.110+, SQLAlchemy 2.x, SQLite (file-backed, no server),
    pytest 8.x for tests. Backend only - no frontend, no container runtime.
    </selected>
    <rationale>
    SQLite rather than PostgreSQL so the whole project runs with no external service:
    a fixture that needs a database server running is a fixture that fails for reasons
    unrelated to what is being tested. No template is referenced, so Layer 0 creates
    directories rather than copying a tree from elsewhere.
    </rationale>
  </tech-stack>

  <features>
    <feature priority="must-have" file="features/save-link.md">
      <name>Save a link</name>
      <summary>Accept a URL with an optional title and store it.</summary>
    </feature>
    <feature priority="must-have" file="features/list-links.md">
      <name>List saved links</name>
      <summary>Return every saved link, newest first.</summary>
    </feature>
    <feature priority="should-have" file="features/tag-links.md">
      <name>Tag links</name>
      <summary>Attach free-text tags to a link and filter the list by tag.</summary>
    </feature>
  </features>

  <dependencies>
    <dependency>
      <name>fastapi</name>
      <version>0.110+</version>
      <purpose>HTTP API framework</purpose>
    </dependency>
    <dependency>
      <name>sqlalchemy</name>
      <version>2.x</version>
      <purpose>ORM and schema definition</purpose>
    </dependency>
    <dependency>
      <name>pytest</name>
      <version>8.x</version>
      <purpose>Test runner used by every task's verification block</purpose>
    </dependency>
  </dependencies>

  <non-functional>
  Scope is capped on purpose. Three features, two models, three endpoints, no
  frontend and no auth - enough to exercise layer planning and the merge queue
  without a sixty-file generation cycle on every iteration. If this fixture starts
  growing, that is a signal to split a second fixture rather than extend this one.
  </non-functional>
</prd>
