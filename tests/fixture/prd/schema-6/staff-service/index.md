<prd>
  <meta>
    <name>Staff Service</name>
    <slug>staff-service</slug>
    <status>in-progress</status>
    <created>2026-08-25</created>
    <updated>2026-08-25</updated>
  </meta>

  <overview>
    <problem>
    A small internal service needs accounts, a way to get data back out, and a stored
    display preference. Today each of those lives in a different script and nothing
    shares an identity.
    </problem>
    <users>
    Staff of one team, signing in with an email and password. No public signup, no
    third-party identity provider.
    </users>
    <value-proposition>
    One service that holds the accounts, returns the records on request, and remembers
    each person's display preference.
    </value-proposition>
  </overview>

  <tech-stack>
    <type>greenfield</type>
    <selected>
    Python 3.11, FastAPI, SQLite, pytest.
    </selected>
    <rationale>
    A conventional stack the team already runs, with SQLite so a developer machine needs
    no database server.
    </rationale>
  </tech-stack>

  <features>
    <feature priority="must-have" file="features/zebra-signin.md">
      <name>Zebra sign-in</name>
      <summary>Email and password sign-in returning a session token.</summary>
    </feature>
    <feature priority="should-have" file="features/walrus-export.md">
      <name>Walrus export</name>
      <summary>Export the caller's records as a CSV download.</summary>
    </feature>
    <feature priority="could-have" file="features/narwhal-theme.md">
      <name>Narwhal theme</name>
      <summary>A stored per-user colour preference applied to responses.</summary>
    </feature>
    <feature priority="wont-have" file="features/quokka-telemetry.md">
      <name>Quokka telemetry</name>
      <summary>Usage analytics sent to a third-party collector.</summary>
    </feature>
  </features>

  <dependencies>
    <dependency>
      <name>fastapi</name>
      <version>0.110+</version>
      <purpose>HTTP API framework</purpose>
    </dependency>
    <dependency>
      <name>pytest</name>
      <version>8.x</version>
      <purpose>Test runner used by every task's verification block</purpose>
    </dependency>
  </dependencies>

  <non-functional>
  Single instance, single database file, no horizontal scaling. Response times are not
  a concern at this size.
  </non-functional>
</prd>
