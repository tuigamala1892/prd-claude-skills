<feature>
  <meta>
    <name>Zebra sign-in</name>
    <slug>zebra-signin</slug>
    <definition>defined</definition>
    <architecturally-significant because="cross-cutting" criteria="1,2"/>
  </meta>

  <user-story>
  As a staff member, I want to sign in with an email and password, so that the service can tell
  my records from anybody else's.
  </user-story>

  <description>
  A POST endpoint that accepts an email and password, verifies them against a stored
  password hash, and returns an opaque session token with an expiry.

  Passwords are stored hashed, never reversibly. The token is opaque to the client:
  no claims are encoded in it, so revoking one is a server-side delete rather than a
  wait for expiry.
  </description>

  <acceptance-criteria>
    <criterion id="1" pattern="event-driven" priority="P0" derived-from="1">
      When a registered account signs in with the correct email and password, the system shall
      return 200 with a token and an expires_at timestamp in the future.
    </criterion>
    <criterion id="2" pattern="unwanted-behaviour" priority="P0" derived-from="2">
      If a sign-in is attempted with a wrong password, then the system shall return 401, issue
      no token, and not disclose which field was wrong.
    </criterion>
  </acceptance-criteria>
</feature>
