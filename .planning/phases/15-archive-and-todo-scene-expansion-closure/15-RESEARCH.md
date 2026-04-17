# Phase 15 Research

Key inputs:

- the shared scene contract already freezes `archive-refresh` and `todo-capture-and-update` as first-wave scene names
- archive refresh has enough substrate for candidate discovery and recommendation-first guidance, but not a separate archive writer surface
- Todo follow-on can safely reuse the current Todo writer as long as candidate creation stays inside the shared contract

Closure strategy:

- expose both scenes through the registry
- keep archive refresh defined on the contract without inventing doc-write behavior
- implement Todo follow-on candidate creation and optional confirmed write through the existing Todo writer path
- add enough regression tests and docs to close VAL-04 and PORT-02 for the milestone