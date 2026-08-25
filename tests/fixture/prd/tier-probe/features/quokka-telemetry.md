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

  **This feature is rejected and must not be built.** It is specified to the same depth
  as the other three deliberately: a won't-have that is obviously unbuildable would let
  `/breakdown` skip it for the wrong reason, and the probe would then prove nothing. It
  is defined, it is buildable, and it is not wanted.
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
