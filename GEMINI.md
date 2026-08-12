# Workspace Custom Rules & Guidelines

When working in this workspace, strictly adhere to the following rules:

## 1. Documentation & Context Preservation
- **Handover files:** Write context incrementally so the next session isn't starting from zero.
- **Decisions.md:** Log the "why" behind every AI decision, not just the "what".
- **Flow.md:** Trace exactly how execution moves between files and functions.
- **Bug.md / Feature.md:** Start-to-finish trails that anyone can pick up cold.
- **Architecture.md:** The system map so nothing gets touched blind.
- **Constraints.md:** The things AI should never touch, spelled out.

## 2. Review & Quality Controls
- **Explicit comments:** Make the flow legible, not just functional.
- **Test checklists:** Proof it works, not just a claim that it does.
- **Rollback plans:** Know your way out before you need it.
- **Read every diff:** Every time.
- **Ask "why" before "what":** Catch bad reasoning before it is 200 lines of code.
- **One change per request:** Small, traceable, reviewable changes.
- **End of session handoff notes:** Write short summary notes to save onboarding time in subsequent sessions.
- **Version pin your context:** Know which model made which call.
- **Own the mental model:** Docs support understanding, they don't replace it.

---
Update the project markdown files regularly as implementation progresses.
