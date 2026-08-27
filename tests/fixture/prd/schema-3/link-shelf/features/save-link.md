<feature>
  <meta>
    <name>Save a link</name>
    <slug>save-link</slug>
    <priority>must-have</priority>
    <definition>defined</definition>
  </meta>

  <description>
  A POST endpoint that accepts a URL and an optional title, stores it, and returns the
  stored record including its generated id and creation timestamp.

  The URL is the only required field. If no title is supplied the field is stored as
  null rather than being derived from the page, because fetching the page would make
  the endpoint depend on the network.
  </description>

  <acceptance-criteria>
    <criterion id="1" pattern="event-driven" priority="P0" derived-from="1">
      When a link is posted with a url and a title, the system shall store it and return 201
      with an integer id, the submitted url and title, and a created_at timestamp.
    </criterion>
    <criterion id="2" pattern="event-driven" priority="P0" derived-from="2">
      When a link is posted with a url and no title, the system shall store it with a null title
      and return 201.
    </criterion>
    <criterion id="3" pattern="unwanted-behaviour" priority="P0" derived-from="3">
      If a link is posted with no url field, then the system shall return 422 and store nothing.
    </criterion>
    <criterion id="4" pattern="unwanted-behaviour" priority="P1" derived-from="4">
      If a link is posted with a url that does not parse as an absolute http or https URL, then
      the system shall return 422 and store nothing.
    </criterion>
  </acceptance-criteria>

  <notes>
  Duplicate URLs are allowed. Deduplication sounds obviously desirable but needs a
  rule for what to do with the existing record's tags and timestamp, and that decision
  is not worth making for a fixture.
  </notes>
</feature>
