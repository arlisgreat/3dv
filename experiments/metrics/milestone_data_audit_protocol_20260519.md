# Milestone Data Audit Protocol

Date: 2026-05-19

Every milestone that consumes generated images must start with a data audit
gate. The gate must be completed and recorded before any GPU reconstruction or
new downstream training run.

## Required Gate

```text
1. State the milestone premise in falsifiable terms.
2. Run structural audit:
   python scripts/audit_data_gate.py --milestone <Gxx> --premise "<premise>" \
     --visual-verdict MANUAL_REVIEW_REQUIRED
3. Make a visual audit sheet for generated PNG candidates:
   python scripts/make_candidate_pool_visual_audit.py --output experiments/figures/<name>.png
4. Inspect the figure with VLM/manual visual checking.
5. Record the verdict under experiments/metrics/.
6. Re-run or update the audit record with the final VLM/manual visual verdict.
7. Update MILESTONES.md before running the experiment.
```

## Gate States

```text
PASS_RECONSTRUCTION_TRAINING:
  The candidates are structurally valid and visually satisfy the stated
  reconstruction premise. This requires explicit VLM/manual evidence.

PASS_DIAGNOSTIC_ONLY:
  The candidates are usable for failure taxonomy or negative diagnostics, but
  must not be called training data.

BLOCKED:
  The candidate pool is missing, structurally invalid, or visually too poor to
  support the milestone premise.
```

## Hard Rule

`experiments/downstream_datasets/` is a candidate-pool export. It is never a
validated training dataset by path alone. A milestone-specific audit verdict is
required each time before using generated candidates for reconstruction.
