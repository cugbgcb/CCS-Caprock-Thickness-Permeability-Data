# Caprock thickness and permeability: study data

Public research data supporting “Thickness-Permeability Trade-off in Geological CO₂ Storage: Quantifying Sealing Performance of Non-Ideal Caprocks”. The paper is being prepared for submission; this repository does not represent an accepted publication.

## Contents

- Exact study input decks (INFILE, INCON, MESH, GENER) and retained FOFT/COFT/GOFT monitor time series for 54 case directories, including continuation directories. Files are deduplicated by SHA-256; `models/manifest.json` preserves original case paths and file names.
- Processed CO₂ mass time series for 51 completed historical cases: one reference and 50 parameter combinations.
- Endpoint summaries, sampled threshold brackets, interval-averaged net migration rates and reference phase partitioning.
- A separate 47-case primary cohort and recomputable criterion brackets, excluding the three continuation cases while retaining all 50 original parameter combinations in the historical archive.
- Selected historical spatial rows documenting negative reconstructed aqueous transport pressure, with explicit qualifications for affected criterion brackets.
- Restoration and metric-recalculation scripts using the Python standard library.

The repository contains study data, not a TOUGH software distribution. Use a separately licensed TOUGH3/ECO2N installation and its required thermophysical tables (CO2TAB) to execute the inputs. Large OUTPUT, complete spatial field exports, raw SAVE, executables and simulator source code are excluded. The working manuscript and experimental GPSFLOW calculations are maintained separately.

## Restore and verify

```sh
python3 scripts/restore_models.py --destination restored-models
python3 scripts/restore_models.py --destination reference --case S0 --inputs-only
python3 scripts/update_metrics.py
python3 scripts/reproduce_primary_cohort.py
python3 scripts/verify_pressure_qualifications.py
```

The restoration script verifies SHA-256 and refuses to overwrite changed files. Restarting a continuation may require its original SAVE file; those files are outside this archive. Model-input availability does not establish grid/time-step convergence or field validation.

## Metric definitions

During injection, migration fraction is 100 times CO₂ inventory above the primary seal divided by injection to date (undefined at zero injection). After 50-year shut-in, this denominator equals the final prescribed injected mass. `R_mig_pct` retains fixed-final-mass normalization for traceability; use `R_mig_current_pct` for transient comparisons. The signed interval-averaged net rate is the change in above-seal inventory divided by elapsed time, expressed in tonnes per year. Migration above the primary seal remains inside the closed model and is not atmospheric release. The selected endpoint criteria are comparative screening thresholds.

The quarter-domain injects 7.92745 kg/s for 50 years and is observed to 100 years, using a 365-day year. The mechanically intact, sub-fracture injection premise is a modeling assumption requiring independent operating-pressure assessment. Constitutive coupling, boundary effects and numerical convergence limit extrapolation.

## Historical numerical controls

The original 51 input decks share a 10 s initial timestep, a 1e7 s maximum timestep and a relative nonlinear tolerance of 1e-5. Three cases include later continuation segments with tolerance 1e-3 and smaller maximum timesteps. See `provenance/historical_numerical_controls.json` for case-specific controls and raw-output join checks. At shared printed times the processed inventory series retain the continuation record; this is documented in `results/historical/provenance.json`. Mass-balance and join checks do not establish timestep, grid or tolerance independence.

Run `python3 scripts/audit_historical_numerical_controls.py` to verify the archived input controls. This writes a separate input-only audit, preserving the full join audit. Optional `--raw-root PATH --output PATH` requires externally retained large OUTPUT files and checks merged inventories against those files without executing a simulator.

## Geometry and interpolation diagnostics

`provenance/geometry_pore_volume_audit.json` records invariant geometry, input-based pore volumes and connection-defined caprock thicknesses for all 51 original cases. Each thickness matches its nominal value; layer counts are discretization information, not proof of grid convergence. Reproduce with `python3 scripts/audit_geometry_pore_volume.py` (standard library).

`results/interpolation_audit/continuation_exclusion.json` retains comparisons of linear/cubic estimated intersections for the original and continuation-excluded case sets. At the four reported permeabilities, the linear 1% intersections remain unchanged to three decimal places; cubic estimates change by at most 1.23%. This is sampling sensitivity, not a tolerance rerun or verification of simulation accuracy. Its automatic triangulation is not fully reproducible from the archived package versions alone: a fresh run differs in two full-50 cubic roots. Reversing sample order also changes some automatic diagonal choices and cubic intersections. The original triangle array was not archived, so the exact cause of the legacy discrepancy cannot be uniquely reconstructed. The historical script and result are retained unchanged; use the explicit-reference successor below for a defined, repeatable interpolation.

### Explicit-reference interpolation successor

`results/interpolation_audit/fixed_log_triangulation.json` stores case identities, exact transformed floating-point coordinates/responses and triangle indices for the original 50, altered-restart-excluded 48 and primary 47 cases. Geometry follows the original CSV order on the delivered-figure plotting stack, without jitter or selection against desired intersections. Supplying these triangles avoids automatic diagonal selection. The native case table and legacy result remain unchanged.

With NumPy and Matplotlib installed, replay into a new file:

```sh
python3 -I scripts/replay_fixed_interpolation.py --reference results/interpolation_audit/fixed_log_triangulation.json --case-summary results/historical/case_summary.csv --output fixed-replay.json
python3 -I scripts/replay_fixed_interpolation.py --reference results/interpolation_audit/fixed_log_triangulation.json --case-summary results/historical/case_summary.csv --reverse-order --output fixed-replay-reversed.json
```

The script refuses an existing output path. `--floor-pct 1e-6` or `--floor-pct 1e-3` recomputes the logarithmic-floor sensitivity with unchanged connectivity. SciPy is not required. `results/interpolation_audit/fixed_intersections.json` records the default-floor replay. All 72 root sets were checked on NumPy 2.4.4 / Matplotlib 3.10.9 and NumPy 2.5.3 / Matplotlib 3.11.2, including reversed case order with mapped triangle indices; their maximum intersection difference was below 3e-14 m. This reports the tested environments, not a guarantee for every platform.

At k = 1e-16 m², the fixed-reference cubic 1% intersections are 8.5126696220 m for all 50, 8.4158200513 m after excluding two altered restarts, and 8.4214174478 m for the primary 47. The four primary-47 linear and cubic 1% intersections and directly sampled brackets are preserved relative to the historical diagnostic. These are numerical interpolation definitions, not additional simulations, physical thresholds, confidence intervals or convergence evidence. The maximum change caused by case exclusion at the four reported cubic 1% intersections remains approximately 1.23%.

## Primary analytical cohort

The current manuscript's primary response-map and criterion analyses use 47 cases without continuation segments. The historical 50-case tables remain intact for traceability. The three exclusions are:

- `Stage01_Scn01-05_H1.57m/k1e-15`
- `Stage02/Stage02_H1.00m/k0.5e-17`
- `Stage02/Stage02_H2.57m/k1e-17`

Run `python3 scripts/reproduce_primary_cohort.py` with the Python standard library. It verifies the historical source hashes and writes `results/primary_response/case_summary.csv`, `threshold_brackets.csv` and `selection.json`. The retained set has 43 cases within 1.57–157 m and 1e-19–1e-15 m² and four exterior guard points. S0 remains a separate reference case. No simulation is executed and no historical input or result is changed.

The four 1% adjacent-thickness brackets are 2.57–6.97 m at 5e-17 m², 4.97–10.97 m at 1e-16 m², 23.7–33.7 m at 5e-16 m² and provisionally 15.7–49.7 m at 1e-15 m². The last bracket shares its lower endpoint with the 5% bracket at that permeability; both carry the pressure qualification below. Within-bracket log-linear estimates are diagnostics, not simulated threshold locations or confidence intervals. The retained cases do not bracket 0.1% at 5e-18 m²; the 0.1% bracket at 1e-17 m² is 1.57–4.97 m.

This script reproduces cohort selection and bracket-table arithmetic, not the interpolated figures. Interpretation remains within the reporting domain; guard points do not justify extrapolation. Removing continuation cases does not establish convergence, thermophysical validity, mechanical feasibility or a regulatory minimum caprock thickness. The public archive contains historical TOUGH inputs/results; experimental GPSFLOW results remain outside this data release.

## Saved-field pressure qualification

The retained historical audit covered 48 cases without continuation segments, including the separate reference, and reported 56 occupied-water states in five cases where `PRES + PCAP_GL` is negative. This is reconstructed aqueous transport pressure; reported primary pressure and occupied-water density remain positive in the selected rows. All 56 rows have zero local aqueous relative permeability, which does not exclude inflow selected from a wet upstream neighbor.

Six of these states occur at the 15.7 m, 1e-15 m² endpoint. The 1% and 5% brackets of 15.7–49.7 m at that permeability remain conditional on capillary and thermophysical validation. Their table values are preserved as historical numerical results, not validated engineering design intervals. Other retained cases also contain flagged states, so qualification is not confined to this one endpoint. Unflagged saved states do not establish full EOS accuracy, unsaved-state validity or numerical convergence.

`results/diagnostics/historical_aqueous_pressure_flags.json` includes the 56 original selected CSV rows, their source-export hashes, input identities, reported scan coverage and machine-readable affected-bracket flags. The standard-library verifier independently recalculates the selected pressure signs and phase/mobility checks, verifies available input objects, and identifies the affected brackets from the unchanged primary tables. Complete spatial exports are not distributed here, so the full scan coverage and absence of additional anomalies cannot be independently reproduced from this subset. No physical case is removed, corrected or recalculated by this verification.
