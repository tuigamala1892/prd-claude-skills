<feature>
  <meta>
    <name>Narwhal theme</name>
    <slug>narwhal-theme</slug>
    <priority>could-have</priority>
    <status>defined</status>
  </meta>

  <description>
  A stored per-user colour preference, set through an endpoint and echoed back on the
  profile response. No rendering: the value is stored and returned, and what a client
  does with it is out of scope.
  </description>

  <acceptance-criteria>
    <criterion id="1">
      <given>A signed-in narwhal caller with no stored preference</given>
      <when>PUT /theme with {"colour": "teal"}</when>
      <then>Response is 200 and a subsequent GET /profile reports colour "teal"</then>
    </criterion>
    <criterion id="2">
      <given>A signed-in narwhal caller</given>
      <when>PUT /theme with {"colour": "not-a-colour"}</when>
      <then>Response is 422 and the stored preference is unchanged</then>
    </criterion>
  </acceptance-criteria>
</feature>
