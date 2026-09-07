<feature>
  <meta>
    <name>List saved links</name>
    <slug>list-links</slug>
    <definition>defined</definition>
    <review by="lee" at="2026-09-07" sha="79818e6a39fd"/>
  </meta>

  <user-story>
  As someone collecting links, I want to see what I have saved, newest first, so that I can find
  the thing I saved this morning without scrolling.
  </user-story>

  <description>
  A GET endpoint returning every saved link as a JSON array, newest first by
  created_at. No pagination: the fixture's scale does not justify it, and adding it
  would introduce a second dimension of behaviour to verify.
  </description>

  <depends-on slug="save-link" kind="data"/>

  <acceptance-criteria>
    <criterion id="1" pattern="ubiquitous" priority="P0" derived-from="1">
      The system shall return 200 and a JSON array from GET /links, empty when no links are
      stored.
    </criterion>
    <criterion id="2" pattern="ubiquitous" priority="P0" derived-from="2">
      The system shall order listed links most recently created first.
    </criterion>
    <criterion id="3" pattern="ubiquitous" priority="P1" derived-from="3">
      The system shall include every stored link in the listing, reporting a null title rather
      than omitting an untitled link.
    </criterion>
    <criterion id="4" pattern="unwanted-behaviour" priority="P0">
      If the stored links cannot be read, then the system shall return 500 and shall not return
      an empty array, so that a failure to read is never reported as an empty shelf.
    </criterion>
  </acceptance-criteria>

  <notes>
    <data-model>
    Reads Link(id, url, title, created_at) -- owned by save-link. This feature owns no
    entity of its own and adds no column; the ordering it guarantees is over created_at.
    </data-model>
    <considerations>
  Ordering is part of the contract, not an incidental detail, so it carries its own
  acceptance criterion. A test that only checks the count would pass against an
  implementation that returns rows in insertion order and silently breaks later.
    </considerations>
  </notes>
</feature>
