<prd>
  <meta>
    <name>Tier Probe</name>
    <slug>tier-probe</slug>
    <status>defined</status>
    <created>2026-08-25</created>
    <updated>2026-08-25</updated>
  </meta>

  <overview>
    <problem>
    This PRD is not a product. It is the smallest input that can answer one question:
    does `/breakdown` build features the product owner explicitly rejected? Finding P1
    says yes, from a static read of every skill; item 21 exists because a passing grep
    is not a run.
    </problem>
    <users>
    The toolchain's own regression suite. Nobody ships this.
    </users>
    <value-proposition>
    One feature per MoSCoW tier, two criteria each, and four slugs that cannot appear
    by coincidence. A generated task mentioning `quokka` came from the won't-have, and
    no other reading is available.
    </value-proposition>
  </overview>

  <tech-stack>
    <type>greenfield</type>
    <selected>
    Python 3.11, FastAPI, SQLite, pytest. Chosen to match the §5.1 fixture so layer
    planning behaves the same way and the probe measures priority handling rather than
    an unfamiliar stack.
    </selected>
    <rationale>
    Deliberately dull. Every choice here is the one that makes the probe's result about
    MoSCoW and nothing else.
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
      <summary>Usage analytics sent to a third-party collector. Explicitly rejected.</summary>
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
  Four features and eight criteria, and it stays that size. P5 says a realistic PRD
  overloads `analyze-prd`, so a probe built at realistic scale would fail for a reason
  that has nothing to do with what it is measuring.
  </non-functional>
</prd>
