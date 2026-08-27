<what-next>
  <meta>
    <prd-slug>link-shelf</prd-slug>
    <status>in-progress</status>
    <last-updated>2026-08-10</last-updated>
    <next-command>/breakdown</next-command>
  </meta>

  <authoring-gaps>
    <summary defined="3" in-progress="0" tbd="0" excluded="0" superseded="0"/>
    <gap slug="tag-links" id="1" kind="decision" raised="2026-08-27"/>
  </authoring-gaps>

  <next-steps>
    <step kind="breakdown">Run /breakdown against index.md to generate tasks</step>
    <step kind="infrastructure">Run /execute against the generated tasks and the fixture project</step>
  </next-steps>

  <session-notes>
  This PRD is a test fixture, not a real product. It exists to exercise the
  toolchain end to end -- see tests/fixture/README.md.

  It carries a top-level &lt;status&gt;in-progress&lt;/status&gt; so that
  `/prd --resume` has something to find. Finding F3 records that resume greps
  what-next.md for exactly that marker while the real PRD carried it in index.md
  instead; this fixture is written the way the skill documents, so a resume test
  against it is meaningful.
  </session-notes>
</what-next>
