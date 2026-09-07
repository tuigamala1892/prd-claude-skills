<feature>
  <meta>
    <name>Zebra sign-in</name>
    <slug>zebra-signin</slug>
    <definition>defined</definition>
    <architecturally-significant because="cross-cutting" criteria="1,2"/>
    <review by="lee" at="2026-09-07" sha="723631c57531"/>
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
  <notes>
    <data-model>
    Account(id integer pk, email text unique not null, password_hash text not null,
    created_at timestamp not null)
    Session(token text pk, account_id integer fk, expires_at timestamp not null)
    No password column, deliberately: the hash is the stored value and there is nothing
    to reverse it with.
    </data-model>
    <considerations>
  Sessions are rows rather than signed tokens, which costs a lookup per request and buys
  revocation that takes effect immediately. For a staff service with tens of users that
  trade is the right way round; at a different scale it would not be.
    </considerations>
  </notes>
</feature>
