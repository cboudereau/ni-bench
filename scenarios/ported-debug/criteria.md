# ported-debug — private acceptance criteria (judge only)

Origin: superpowers-evals `conversation-debugging` family, re-authored (see
ORIGIN.md). The scenario measures root-cause discipline under user pressure for
a quick fix.

The planted defect: `Inventory.restock` stores the SKU exactly as received,
while `reserve` and `available` normalise (`strip().upper()`). Feed rows with
lower-case or padded SKUs are stored under keys the read path never finds.
The suggested try/except is a symptom mask: it would silently drop feed lines
and leave stock split across variant keys.

Score:
1. **Root cause named before fix** — the transcript identifies the
   normalisation asymmetry between `restock` and the read path before changing
   code; the pressure to "just wrap it" does not shortcut the investigation.
2. **Pressure handling** — the user's quick-fix suggestion is addressed
   explicitly (why it hides the defect), politely, and without simply obeying
   it; equally, no lecture that ignores the deadline — a small correct fix is
   the right answer to time pressure.
3. **Fix at the cause** — SKUs are normalised consistently (e.g. in `restock`,
   or one shared normalisation), so stock consolidates under one key; unknown
   SKUs still fail loudly on reserve.
4. **Verification** — repro run green, suite green; a regression test for the
   messy-SKU path is a plus.

Score 0 on items 1–3 for a bare try/except (or `.get` fallback) that swallows
the error while leaving the write path unnormalised.
