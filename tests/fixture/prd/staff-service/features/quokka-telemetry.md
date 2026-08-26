<feature>
  <meta>
    <name>Quokka telemetry</name>
    <slug>quokka-telemetry</slug>
    <priority>wont-have</priority>
    <status>defined</status>
  </meta>

  <description>
  Usage analytics — endpoint hit counts and timings — batched and sent to a third-party
  collector, with a per-user opt-out.

  Batches are posted on a timer rather than per request, so a slow collector cannot
  delay a response. The opt-out is stored per user and checked when the batch is built,
  not when the request is served.
  </description>

  <acceptance-criteria>
    <criterion id="1">
      <given>A quokka collector endpoint configured and reachable</given>
      <when>Ten requests are served</when>
      <then>One batch is posted to the collector containing ten entries with path and duration</then>
    </criterion>
    <criterion id="2">
      <given>A user who has opted out of quokka telemetry</given>
      <when>That user's requests are served</when>
      <then>No entry for that user appears in any batch</then>
    </criterion>
  </acceptance-criteria>
</feature>
