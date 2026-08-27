<feature>
  <meta>
    <name>Walrus export</name>
    <slug>walrus-export</slug>
    <priority>should-have</priority>
    <definition>defined</definition>
  </meta>

  <description>
  A GET endpoint that returns the caller's records as CSV, with a header row and one
  row per record, served as a file download rather than a JSON body.
  </description>

  <acceptance-criteria>
    <criterion id="1" pattern="event-driven" priority="P1" derived-from="1">
      When a signed-in caller requests an export, the system shall return 200 with content-type
      text/csv and a header row followed by one row per record.
    </criterion>
    <criterion id="2" pattern="unwanted-behaviour" priority="P1" derived-from="2">
      If a signed-in caller with no records requests an export, then the system shall return 200
      with the header row alone rather than 404.
    </criterion>
  </acceptance-criteria>
</feature>
