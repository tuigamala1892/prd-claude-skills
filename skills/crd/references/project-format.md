# PROJECT.md Format Specification

PROJECT.md provides context about an existing codebase for efficient change requests. It contains human-readable documentation and machine-readable structured data.

## File Location

`{project_root}/PROJECT.md`

## Structure

```markdown
# Project: {name}

## Overview
{Brief description of what this project does}

## Architecture

### Tech Stack
- Backend: {framework} ({language} {version})
- Frontend: {framework} + {bundler}
- Database: {database} with {ORM}
- Auth: {auth mechanism}

### Component Structure
```
{directory tree with annotations}
```

### Key Patterns
- {Pattern 1}: {Description}
- {Pattern 2}: {Description}

## Context Metadata
<!-- Machine-readable section - do not edit manually -->
<project-context version="1.0">
  {structured XML content}
</project-context>
```

## Machine-Readable Section

### Root Element

```xml
<project-context version="1.0">
  <meta>...</meta>
  <features>...</features>
  <api-registry>...</api-registry>        <!-- any number of registries; see below -->
  <schema-registry>...</schema-registry>
</project-context>
```

`meta` and `features` are required, and **at least one registry** is required. Which registry is
the project's business, not this format's — see [The registry set is open](#the-registry-set-is-open).

### The registry set is open

`api-registry` plus `schema-registry` is REST plus relational: the right pair for the project
this toolchain was built for, and the wrong pair for most others. A CLI's primary contract is its
subcommands; an event-driven system's is its published events; a microservice estate's is its
service boundaries. So the pair is a **default, not the schema**.

| Registry | Records | Natural to |
|---|---|---|
| `<api-registry>` | method, path, request, response | REST |
| `<schema-registry>` | model, table, fields | relational |
| `<event-registry>` | event, version, payload, producers, consumers | event-driven |
| `<command-registry>` | subcommand, flags, exit codes, output format | CLI |
| `<service-registry>` | service, owns, contracts, deployable unit | microservices |
| `<screen-registry>` | screen, route, view-model | mobile / SPA |

A registry outside these six is accepted; it simply has no shipped reader.

`check-project-md.py` requires **any one** rather than two particular ones. The two names were a
proxy for *a consumer can read this*, and that proxy stays honest while asking for one. Each
consumer then refuses on its own behalf: `crd-impact-analysis` says clearly when the specific
registry it is about to read is absent, rather than this file mandating a shape for it.

### Relationship to `architecture.md`

The same registry elements, with the same content, are root children of
[`architecture.md`](../../breakdown/references/architecture-format.md) — the **prescriptive**
counterpart to this **descriptive** file. That is deliberate: item 26 seeds a greenfield
`PROJECT.md` from `architecture.md`, and sharing the element names and nesting level makes that
seeding a subtree **copy** rather than a transform.

| | `architecture.md` | `PROJECT.md` |
|---|---|---|
| Direction | prescriptive — what must be true | descriptive — what is true |
| Derived from | a conversation, before code exists | the code |
| Also carries | `<rules>`, `<principles>` | `<features>` |

### Meta Section

```xml
<meta>
  <last-updated>2026-01-12T10:30:00Z</last-updated>
  <last-context-hash>abc123def456</last-context-hash>
  <prd-path>docs/prd/my-project/index.md</prd-path>  <!-- optional -->
</meta>
```

| Field | Required | Description |
|-------|----------|-------------|
| `last-updated` | Yes | ISO 8601 timestamp of last context update |
| `last-context-hash` | Yes | Git commit hash when context was captured |
| `prd-path` | No | Path to PRD if project was created with /prd |

### Features Section

```xml
<features>
  <feature id="auth" status="complete">
    <name>User Authentication</name>
    <files>src/api/auth.py, src/services/auth.py, src/models/user.py</files>
    <crd-ref>docs/crd/auth-enhancement.md</crd-ref>  <!-- optional -->
  </feature>

  <feature id="settings" status="complete">
    <name>User Settings</name>
    <files>src/api/settings.py, src/components/SettingsModal.tsx</files>
  </feature>
</features>
```

| Attribute/Element | Required | Description |
|-------------------|----------|-------------|
| `id` | Yes | Unique slug identifier — core [§1](../../../schema/core.md#1-identity) |
| `status` | Yes | `complete`, `partial`, `planned` — core [§3](../../../schema/core.md#3-status), fourth row |
| `name` | Yes | Human-readable feature name |
| `files` | Yes | Comma-separated list of primary files |
| `crd-ref` | No | Reference to CRD that created/modified this feature |

**This `status` records how much of the feature exists in code, and it is the only one of the
four that does.** A PRD feature file's `<status>` says how completely the feature is *defined* —
a fully specified feature that nobody has started is `defined` there and `planned` here, and both
are correct at once. `PROJECT.md` is descriptive: it is written from the code, so a value here
that the code does not support is a bug in the investigation, not a plan.

### API Registry Section

```xml
<api-registry>
  <endpoint method="POST" path="/api/auth/login">
    <request>{ email: string, password: string }</request>
    <response>{ token: string, refresh_token: string, user: User }</response>
    <auth>none</auth>
  </endpoint>

  <endpoint method="GET" path="/api/users/me">
    <request>none</request>
    <response>{ id: string, email: string, settings: object }</response>
    <auth>bearer</auth>
  </endpoint>

  <endpoint method="PUT" path="/api/settings">
    <request>{ settings: object }</request>
    <response>{ success: boolean }</response>
    <auth>bearer</auth>
  </endpoint>
</api-registry>
```

| Attribute/Element | Required | Description |
|-------------------|----------|-------------|
| `method` | Yes | HTTP method (GET, POST, PUT, DELETE, PATCH) |
| `path` | Yes | API path |
| `request` | Yes | Request body shape or "none" |
| `response` | Yes | Response body shape |
| `auth` | No | Authentication requirement (none, bearer, api-key) |

### Schema Registry Section

```xml
<schema-registry>
  <model name="User" table="users">
    <field name="id" type="uuid" primary="true"/>
    <field name="email" type="string" unique="true"/>
    <field name="password_hash" type="string"/>
    <field name="settings" type="jsonb"/>
    <field name="created_at" type="timestamp"/>
  </model>

  <model name="Session" table="sessions">
    <field name="id" type="uuid" primary="true"/>
    <field name="user_id" type="uuid" foreign="users.id"/>
    <field name="token" type="string" unique="true"/>
    <field name="expires_at" type="timestamp"/>
  </model>
</schema-registry>
```

| Attribute | Required | Description |
|-----------|----------|-------------|
| `name` | Yes | Model/class name |
| `table` | Yes | Database table name |
| Field `name` | Yes | Column/field name |
| Field `type` | Yes | Data type (uuid, string, integer, boolean, timestamp, jsonb, etc.) |
| Field `primary` | No | "true" if primary key |
| Field `unique` | No | "true" if unique constraint |
| Field `foreign` | No | Foreign key reference (table.column) |

## Example Complete PROJECT.md

```markdown
# Project: My E-commerce App

## Overview
A full-stack e-commerce application with user authentication, product catalog, and order management.

## Architecture

### Tech Stack
- Backend: FastAPI (Python 3.11)
- Frontend: React + Vite + TypeScript
- Database: PostgreSQL with SQLAlchemy ORM
- Auth: JWT with refresh tokens

### Component Structure
```
src/
├── api/              # FastAPI route handlers
│   ├── auth.py       # Authentication endpoints
│   ├── products.py   # Product CRUD
│   └── orders.py     # Order management
├── models/           # SQLAlchemy models
├── services/         # Business logic layer
├── frontend/         # React application
│   ├── components/   # Reusable components
│   ├── pages/        # Page components
│   └── hooks/        # Custom hooks
└── tests/            # Test suites
```

### Key Patterns
- Repository pattern for data access
- Service layer for business logic
- React Query for server state management
- JWT stored in httpOnly cookies

## Context Metadata
<!-- Machine-readable section - do not edit manually -->
<project-context version="1.0">
  <meta>
    <last-updated>2026-01-12T10:30:00Z</last-updated>
    <last-context-hash>abc123def456789</last-context-hash>
  </meta>

  <features>
    <feature id="auth" status="complete">
      <name>User Authentication</name>
      <files>src/api/auth.py, src/models/user.py, src/frontend/pages/Login.tsx</files>
    </feature>
    <feature id="products" status="complete">
      <name>Product Catalog</name>
      <files>src/api/products.py, src/models/product.py, src/frontend/pages/Products.tsx</files>
    </feature>
  </features>

  <api-registry>
    <endpoint method="POST" path="/api/auth/login">
      <request>{ email: string, password: string }</request>
      <response>{ token: string, user: User }</response>
      <auth>none</auth>
    </endpoint>
    <endpoint method="GET" path="/api/products">
      <request>none</request>
      <response>{ products: Product[], total: number }</response>
      <auth>none</auth>
    </endpoint>
  </api-registry>

  <schema-registry>
    <model name="User" table="users">
      <field name="id" type="uuid" primary="true"/>
      <field name="email" type="string" unique="true"/>
      <field name="password_hash" type="string"/>
    </model>
    <model name="Product" table="products">
      <field name="id" type="uuid" primary="true"/>
      <field name="name" type="string"/>
      <field name="price" type="decimal"/>
      <field name="stock" type="integer"/>
    </model>
  </schema-registry>
</project-context>
```

## Parsing Guidelines

### For Context Check

1. Find `<last-context-hash>` tag
2. Extract hash value
3. Compare with `git rev-parse HEAD`

### For Feature Lookup

1. Parse `<features>` section
2. Build map of `id` → feature object
3. Use for impact analysis matching

### For API Lookup

1. Parse `<api-registry>` section
2. Index by `method + path`
3. Use for endpoint impact detection

### For Schema Lookup

1. Parse `<schema-registry>` section
2. Index by model `name` and `table`
3. Use for migration impact detection

## Version History

| Version | Changes |
|---------|---------|
| 1.0 | Initial format specification |
| 1.0 | Registry set opened; any one registry required rather than the REST/relational pair (plan item 25, review finding R8). No element changed shape, so existing files stay valid |
