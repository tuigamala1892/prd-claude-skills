<feature>
  <meta>
    <name>List saved links</name>
    <slug>list-links</slug>
    <definition>defined</definition>
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
  </acceptance-criteria>

  <notes>
    <considerations>
  Ordering is part of the contract, not an incidental detail, so it carries its own
  acceptance criterion. A test that only checks the count would pass against an
  implementation that returns rows in insertion order and silently breaks later.
    </considerations>
  </notes>
</feature>
