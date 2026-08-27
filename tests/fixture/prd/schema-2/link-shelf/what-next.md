<what-next>
  <status>in-progress</status>
  <last-updated>2026-08-10</last-updated>

  <tbd-items>
    <item section="features" ref="features/tag-links.md">
      Decide whether tag matching should be case-folded. Currently specified as
      case-sensitive so the behaviour is at least pinned down.
    </item>
  </tbd-items>

  <next-steps>
    <step>Run /breakdown against index.md to generate tasks</step>
    <step>Run /execute against the generated tasks and the fixture project</step>
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
