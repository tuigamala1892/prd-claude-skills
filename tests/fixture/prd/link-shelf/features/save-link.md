<feature>
  <meta>
    <name>Save a link</name>
    <slug>save-link</slug>
    <priority>must-have</priority>
    <status>defined</status>
  </meta>

  <description>
  A POST endpoint that accepts a URL and an optional title, stores it, and returns the
  stored record including its generated id and creation timestamp.

  The URL is the only required field. If no title is supplied the field is stored as
  null rather than being derived from the page, because fetching the page would make
  the endpoint depend on the network.
  </description>

  <acceptance-criteria>
    <criterion id="1">
      <given>An empty database</given>
      <when>POST /links with {"url": "https://example.com", "title": "Example"}</when>
      <then>Response is 201 with an integer id, the submitted url and title, and a created_at timestamp</then>
    </criterion>
    <criterion id="2">
      <given>An empty database</given>
      <when>POST /links with {"url": "https://example.com"} and no title</when>
      <then>Response is 201 and the stored title is null</then>
    </criterion>
    <criterion id="3">
      <given>An empty database</given>
      <when>POST /links with {"title": "No URL here"} and no url field</when>
      <then>Response is 422 and nothing is stored</then>
    </criterion>
    <criterion id="4">
      <given>An empty database</given>
      <when>POST /links with {"url": "not-a-url"}</when>
      <then>Response is 422 - the url field must parse as an absolute http or https URL</then>
    </criterion>
  </acceptance-criteria>

  <notes>
  Duplicate URLs are allowed. Deduplication sounds obviously desirable but needs a
  rule for what to do with the existing record's tags and timestamp, and that decision
  is not worth making for a fixture.
  </notes>
</feature>
