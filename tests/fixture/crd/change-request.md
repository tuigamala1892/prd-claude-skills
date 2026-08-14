# Change request: archive links instead of deleting them

Written the way a stakeholder would write it — prose, not a specification. Turning this into
a structured CRD is `/crd`'s job, and handing it something already structured would test
nothing.

---

At the moment deleting a link is permanent, and people keep asking for the one they deleted
last week. We'd like to keep them instead of losing them.

What we want:

- Archiving a link hides it from the normal list, but doesn't destroy it.
- You can see what's archived, and put one back.
- Archived links shouldn't show up in searches or tag filters by default, but there should be
  some way to include them if you really want to.
- Tags on an archived link should stay attached, so restoring gets you back exactly what you
  had.

We'd rather not lose the existing delete for now — some things genuinely should go — but it
should be the unusual choice, not the default one.

Nothing here needs to be fast. The library is a few thousand links at most.
