# Add or change a feature

1. Describe it as the owner's workflow. Does it change the memorized flow? Then ask first.
   Would an elder find it hard? Then simplify or leave it out (owner allows removing).
2. Data first in `app/db.py` with tests; keep tables compatible with old versions
   (`workflows/data-changes.md`).
3. UI with existing components (`reference/design-system.md`); routine feedback via `Toast`.
4. Verify: tests → screenshots → `tools/bench.py` if lists/queries changed → Windows exe.
5. Update `readme.md` / `CLAUDE.md` for user-visible changes; retro.
