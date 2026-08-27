<feature>
  <meta>
    <name>List saved links</name>
    <slug>list-links</slug>
    <priority>must-have</priority>
    <definition>defined</definition>
  </meta>

  <description>
  A GET endpoint returning every saved link as a JSON array, newest first by
  created_at. No pagination: the fixture's scale does not justify it, and adding it
  would introduce a second dimension of behaviour to verify.
  </description>

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
  Ordering is part of the contract, not an incidental detail, so it carries its own
  acceptance criterion. A test that only checks the count would pass against an
  implementation that returns rows in insertion order and silently breaks later.
  </notes>
</feature>
