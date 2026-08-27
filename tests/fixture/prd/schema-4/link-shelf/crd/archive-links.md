<crd>
  <meta>
    <name>Archive links instead of deleting them</name>
    <slug>archive-links</slug>
    <type>feature-modify</type>
    <created>2026-08-20</created>
    <workflow>ready</workflow>
  </meta>

  <context>
    <project-ref>PROJECT.md</project-ref>
    <prd-ref>docs/prd/link-shelf/index.md</prd-ref>
    <related-features>
      <feature-ref id="save-link">Deletion lives here today</feature-ref>
      <feature-ref id="list-links">The list must stop showing archived links</feature-ref>
      <feature-ref id="tag-links">Tags stay attached across an archive and a restore</feature-ref>
    </related-features>
  </context>

  <change-request>
    <summary>
    Archiving hides a link from the normal list without destroying it, and an archived link
    can be restored with its tags intact.
    </summary>
    <motivation>
    Deletion is permanent and people keep asking for links they removed last week. Delete
    should stay available and become the unusual choice rather than the default one.
    </motivation>
  </change-request>

  <impact-analysis>
    <affected-files>
      <file action="modify">src/models/link.py</file>
      <file action="modify">src/api/links.py</file>
      <file action="create">migrations/003_archive_links.sql</file>
      <file action="modify">src/api/tags.py</file>
    </affected-files>
    <affected-features>
      <feature id="save-link">Delete becomes archive; hard delete stays behind a flag</feature>
      <feature id="list-links">Default listing excludes archived links</feature>
      <feature id="tag-links">Tag filters exclude archived links unless asked</feature>
    </affected-features>
    <affected-contracts>
      <contract kind="api">DELETE /links/{id} changes meaning</contract>
      <contract kind="schema">links gains an archived_at column</contract>
    </affected-contracts>
    <breaking-changes>
      <change severity="minor">
      DELETE /links/{id} archives rather than destroys. Callers relying on the row being gone
      see it again through the archived listing.
      </change>
    </breaking-changes>
    <scope>medium</scope>
    <confidence>high</confidence>
  </impact-analysis>

  <requirements>
    <requirement id="1" priority="must-have">
    An archived link is hidden from the default listing but retained in storage.
    </requirement>
    <requirement id="2" priority="must-have">
    Archived links can be listed on their own, and any one of them restored.
    </requirement>
    <requirement id="3" priority="should-have">
    Search and tag filters exclude archived links unless the caller asks for them.
    </requirement>
    <requirement id="4" priority="could-have">
    Hard deletion remains available for links that genuinely should go.
    </requirement>
  </requirements>

  <acceptance-criteria>
    <criterion id="1" pattern="event-driven" priority="P0">
    When a link is archived, the system shall retain its tag associations unchanged.
    </criterion>
    <criterion id="2" pattern="unwanted-behaviour" priority="P0">
    If a restore names a link that was never archived, then the system shall reject the
    request and leave the link untouched.
    </criterion>
  </acceptance-criteria>
</crd>
