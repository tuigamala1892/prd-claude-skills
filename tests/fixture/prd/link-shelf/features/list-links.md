<feature>
  <meta>
    <name>List saved links</name>
    <slug>list-links</slug>
    <priority>must-have</priority>
    <status>defined</status>
  </meta>

  <description>
  A GET endpoint returning every saved link as a JSON array, newest first by
  created_at. No pagination: the fixture's scale does not justify it, and adding it
  would introduce a second dimension of behaviour to verify.
  </description>

  <acceptance-criteria>
    <criterion id="1">
      <given>An empty database</given>
      <when>GET /links</when>
      <then>Response is 200 with an empty JSON array</then>
    </criterion>
    <criterion id="2">
      <given>Three links saved at distinct times</given>
      <when>GET /links</when>
      <then>Response is 200 with all three, ordered most recently created first</then>
    </criterion>
    <criterion id="3">
      <given>One saved link with a title and one without</given>
      <when>GET /links</when>
      <then>Both appear; the untitled one has title null rather than being omitted</then>
    </criterion>
  </acceptance-criteria>

  <notes>
  Ordering is part of the contract, not an incidental detail, so it carries its own
  acceptance criterion. A test that only checks the count would pass against an
  implementation that returns rows in insertion order and silently breaks later.
  </notes>
</feature>
