<feature>
  <meta>
    <name>Quokka telemetry</name>
    <slug>quokka-telemetry</slug>
    <definition>in-progress</definition>
    <architecturally-significant because="external-dependency" criteria="1"/>
  </meta>

  <user-story>
  As the operations team, I want per-request timings, so that we can see which endpoints are
  slow before anybody reports it.
  </user-story>

  <description>
  Usage analytics — endpoint hit counts and timings — batched and sent to a third-party
  collector, with a per-user opt-out.

  Batches are posted on a timer rather than per request, so a slow collector cannot
  delay a response. The opt-out is stored per user and checked when the batch is built,
  not when the request is served.
  </description>

  <acceptance-criteria>
    <criterion id="1" pattern="state-driven" priority="P2" derived-from="1">
      While a collector endpoint is configured and reachable, the system shall post one batch
      per ten served requests, each entry carrying the path and duration.
    </criterion>
    <criterion id="2" pattern="optional-feature" priority="P2" derived-from="2">
      Where a user has opted out of telemetry, the system shall include no entry for that user
      in any batch.
    </criterion>
  </acceptance-criteria>

  <gaps>
    <gap id="1" kind="dependency" raised="2026-08-27">
    The collector endpoint does not exist yet, so nothing can be posted to it and the batching
    cannot be exercised end to end.
    </gap>
    <gap id="2" kind="specification" raised="2026-08-27">
    How a user opts out is unspecified -- a stored preference, a header, or a deployment-wide
    switch are all consistent with the criteria.
    </gap>
  </gaps>
</feature>
