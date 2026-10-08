# Caprock thickness and permeability: study data

Public research data supporting “Thickness-Permeability Trade-off in Geological CO₂ Storage: Quantifying Sealing Performance of Non-Ideal Caprocks”. The paper is being prepared for submission; this repository does not represent an accepted publication.

## Contents

- Exact study input decks (INFILE, INCON, MESH, GENER) and retained FOFT/COFT/GOFT monitor time series for 54 case directories, including continuation directories. Files are deduplicated by SHA-256; `models/manifest.json` preserves original case paths and file names.
- Processed CO₂ mass time series for 51 completed historical cases: one reference and 50 parameter combinations.
- Endpoint summaries, sampled threshold brackets, interval-averaged net migration rates and reference phase partitioning.
- Restoration and metric-recalculation scripts using the Python standard library.

The repository contains study data, not a TOUGH software distribution. Use a separately licensed TOUGH3/ECO2N installation and its required thermophysical tables (CO2TAB) to execute the inputs. Large OUTPUT, spatial field exports, raw SAVE, executables and simulator source code are excluded. The working manuscript and experimental GPSFLOW calculations are maintained separately.

## Restore and verify

```sh
python3 scripts/restore_models.py --destination restored-models
python3 scripts/restore_models.py --destination reference --case S0 --inputs-only
python3 scripts/update_metrics.py
```

The restoration script verifies SHA-256 and refuses to overwrite changed files. Restarting a continuation may require its original SAVE file; those files are outside this archive. Model-input availability does not establish grid/time-step convergence or field validation.

## Metric definitions

During injection, migration fraction is 100 times CO₂ inventory above the primary seal divided by injection to date (undefined at zero injection). After 50-year shut-in, this denominator equals the final prescribed injected mass. `R_mig_pct` retains fixed-final-mass normalization for traceability; use `R_mig_current_pct` for transient comparisons. The signed interval-averaged net rate is the change in above-seal inventory divided by elapsed time, expressed in tonnes per year. Migration above the primary seal remains inside the closed model and is not atmospheric release. The selected endpoint criteria are comparative screening thresholds.

The quarter-domain injects 7.92745 kg/s for 50 years and is observed to 100 years, using a 365-day year. The mechanically intact, sub-fracture injection premise is a modeling assumption requiring independent operating-pressure assessment. Constitutive coupling, boundary effects and numerical convergence limit extrapolation.

## Historical numerical controls

The original 51 input decks share a 10 s initial timestep, a 1e7 s maximum timestep and a relative nonlinear tolerance of 1e-5. Three cases include later continuation segments with tolerance 1e-3 and smaller maximum timesteps. See `provenance/historical_numerical_controls.json` for case-specific controls and raw-output join checks. At shared printed times the processed inventory series retain the continuation record; this is documented in `results/historical/provenance.json`. Mass-balance and join checks do not establish timestep, grid or tolerance independence.

Run `python3 scripts/audit_historical_numerical_controls.py` to verify the archived input controls. This writes a separate input-only audit, preserving the full join audit. Optional `--raw-root PATH --output PATH` requires externally retained large OUTPUT files and checks merged inventories against those files without executing a simulator.
