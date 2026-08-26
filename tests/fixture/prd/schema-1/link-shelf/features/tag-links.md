<feature>
  <meta>
    <name>Tag links</name>
    <slug>tag-links</slug>
    <priority>should-have</priority>
    <status>defined</status>
  </meta>

  <description>
  Attach zero or more free-text tags to a link, and filter the list endpoint by tag.

  Tags are a separate table with a many-to-many join to links, not a comma-separated
  string column. This is the one place the fixture deliberately requires a real
  relationship: a single-table shortcut would make the data-model layer trivial and
  the fixture would stop exercising the part of layer planning most likely to break.
  </description>

  <acceptance-criteria>
    <criterion id="1">
      <given>A saved link with no tags</given>
      <when>POST /links/{id}/tags with {"tags": ["reading", "python"]}</when>
      <then>Response is 200 and the link now reports both tags</then>
    </criterion>
    <criterion id="2">
      <given>A link already tagged "python"</given>
      <when>POST /links/{id}/tags with {"tags": ["python"]}</when>
      <then>Response is 200 and the tag appears once, not twice</then>
    </criterion>
    <criterion id="3">
      <given>Two links tagged "python" and one tagged "cooking"</given>
      <when>GET /links?tag=python</when>
      <then>Response is 200 with exactly the two python-tagged links</then>
    </criterion>
    <criterion id="4">
      <given>Any database state</given>
      <when>POST /links/{id}/tags for an id that does not exist</when>
      <then>Response is 404 and no tag rows are created</then>
    </criterion>
  </acceptance-criteria>

  <notes>
  Tag names are matched case-sensitively. Case folding is a reasonable product
  decision but it is not free to verify, and leaving it explicit here stops an
  implementer inventing either behaviour and calling it correct.

  This feature is should-have rather than must-have so layer planning has to decide
  where a lower-priority item lands, rather than treating every feature identically.
  </notes>
</feature>
