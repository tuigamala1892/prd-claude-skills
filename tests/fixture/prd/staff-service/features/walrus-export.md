<feature>
  <meta>
    <name>Walrus export</name>
    <slug>walrus-export</slug>
    <priority>should-have</priority>
    <status>defined</status>
  </meta>

  <description>
  A GET endpoint that returns the caller's records as CSV, with a header row and one
  row per record, served as a file download rather than a JSON body.
  </description>

  <acceptance-criteria>
    <criterion id="1">
      <given>A signed-in walrus caller with three records</given>
      <when>GET /export</when>
      <then>Response is 200, content-type is text/csv, and the body has a header row plus three rows</then>
    </criterion>
    <criterion id="2">
      <given>A signed-in walrus caller with no records</given>
      <when>GET /export</when>
      <then>Response is 200 with the header row alone, not a 404</then>
    </criterion>
  </acceptance-criteria>
</feature>
