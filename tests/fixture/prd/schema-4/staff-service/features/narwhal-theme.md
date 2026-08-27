<feature>
  <meta>
    <name>Narwhal theme</name>
    <slug>narwhal-theme</slug>
    <definition>defined</definition>
  </meta>

  <user-story>
  As a staff member, I want to choose an interface colour, so that the service is comfortable to
  look at for a whole shift.
  </user-story>

  <description>
  A stored per-user colour preference, set through an endpoint and echoed back on the
  profile response. No rendering: the value is stored and returned, and what a client
  does with it is out of scope.
  </description>

  <depends-on slug="zebra-signin" kind="runtime"/>

  <acceptance-criteria>
    <criterion id="1" pattern="event-driven" priority="P2" derived-from="1">
      When a signed-in caller sets a theme colour, the system shall store it and report it from
      the profile endpoint.
    </criterion>
    <criterion id="2" pattern="unwanted-behaviour" priority="P2" derived-from="2">
      If a theme colour outside the accepted set is submitted, then the system shall return 422
      and leave the stored preference unchanged.
    </criterion>
  </acceptance-criteria>
</feature>
