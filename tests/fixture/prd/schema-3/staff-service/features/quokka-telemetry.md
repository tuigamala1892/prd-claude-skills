<feature>
  <meta>
    <name>Quokka telemetry</name>
    <slug>quokka-telemetry</slug>
    <priority>wont-have</priority>
    <definition>defined</definition>
  </meta>

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
</feature>
