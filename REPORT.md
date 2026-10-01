# ni-bench REPORT

## Run metadata

| Field | Value |
|---|---|
| Subject model | unknown |
| Judge model | claude-sonnet-5-5 |
| Simulator model | claude-haiku-4-5-20251001 |
| claude-code | 2.1.285 |
| Plugins | superpowers 6.4.2, ni 1.5.0, openspec 1.13.2 |
| n (trials per arm x scenario) | unknown |
| Verbosity config | baseline: default; openspec: OPENSPEC_TELEMETRY=0; superpowers: default; ni: terse=full |
| Date | unknown |

Resource percents are relative to this arm set (kpi-scoring ADR): the best arm scores 100%; lower raw is better.

## Notes

- `plan_words` is scored only among arms whose `plan_quality` is at least 50 (quality floor, kpi-scoring ADR); arms below the floor show the raw value only.
- Indeterminate trials are excluded from medians and pass-rates; the `indeterminate` row counts them per arm (FR7).
- Blinding residual risk (NFR4): arm identifiers are redacted from judge input, but artifact structure (directory layout, plan format) can still leak arm identity despite blinding.
