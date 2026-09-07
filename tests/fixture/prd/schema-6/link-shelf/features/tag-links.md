<feature>
  <meta>
    <name>Tag links</name>
    <slug>tag-links</slug>
    <definition>defined</definition>
    <review by="lee" at="2026-09-07" sha="0a8e14b51375"/>
  </meta>

  <user-story>
  As someone collecting links, I want to tag what I save and filter by tag, so that a shelf of
  two hundred links stays usable.
  </user-story>

  <description>
  Attach zero or more free-text tags to a link, and filter the list endpoint by tag.

  Tags are a separate table with a many-to-many join to links, not a comma-separated
  string column. This is the one place the fixture deliberately requires a real
  relationship: a single-table shortcut would make the data-model layer trivial and
  the fixture would stop exercising the part of layer planning most likely to break.
  </description>

  <depends-on slug="save-link" kind="data"/>

  <acceptance-criteria>
    <criterion id="1" pattern="event-driven" priority="P0" derived-from="1">
      When tags are posted to an existing link, the system shall attach them and return 200 with
      the link reporting every attached tag.
    </criterion>
    <criterion id="2" pattern="event-driven" priority="P1" derived-from="2">
      When a tag already attached to a link is posted again, the system shall return 200 and
      leave the tag attached exactly once.
    </criterion>
    <criterion id="3" pattern="event-driven" priority="P0" derived-from="3">
      When links are listed with a tag filter, the system shall return exactly the links
      carrying that tag.
    </criterion>
    <criterion id="4" pattern="unwanted-behaviour" priority="P0" derived-from="4">
      If tags are posted to a link id that does not exist, then the system shall return 404 and
      create no tag rows.
    </criterion>
  </acceptance-criteria>

  <gaps>
    <gap id="1" kind="decision" raised="2026-08-27">
    Whether a tag with no remaining links is deleted or kept is undecided. Keeping them makes an
    autocomplete list easy and lets the list rot.
    </gap>
  </gaps>

  <notes>
    <data-model>
    Tag(id integer pk, name text unique not null)
    LinkTag(link_id fk Link.id, tag_id fk Tag.id, primary key both)
    </data-model>
    <considerations>
  Tag names are matched case-sensitively. Case folding is a reasonable product
  decision but it is not free to verify, and leaving it explicit here stops an
  implementer inventing either behaviour and calling it correct.

  This feature is should-have rather than must-have so layer planning has to decide
  where a lower-priority item lands, rather than treating every feature identically.
    </considerations>
  </notes>
</feature>
