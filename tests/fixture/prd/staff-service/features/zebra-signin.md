<feature>
  <meta>
    <name>Zebra sign-in</name>
    <slug>zebra-signin</slug>
    <priority>must-have</priority>
    <status>defined</status>
  </meta>

  <description>
  A POST endpoint that accepts an email and password, verifies them against a stored
  password hash, and returns an opaque session token with an expiry.

  Passwords are stored hashed, never reversibly. The token is opaque to the client:
  no claims are encoded in it, so revoking one is a server-side delete rather than a
  wait for expiry.
  </description>

  <acceptance-criteria>
    <criterion id="1">
      <given>A registered zebra account with a known password</given>
      <when>POST /signin with the correct email and password</when>
      <then>Response is 200 with a token string and an expires_at timestamp in the future</then>
    </criterion>
    <criterion id="2">
      <given>A registered zebra account</given>
      <when>POST /signin with the correct email and a wrong password</when>
      <then>Response is 401, no token is issued, and the body does not say which field was wrong</then>
    </criterion>
  </acceptance-criteria>
</feature>
