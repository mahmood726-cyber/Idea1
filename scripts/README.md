# CNMA Platform - Analysis Scripts

This directory contains scripts for validation, sensitivity analyses, and other computational studies required for publication.

## Available Scripts

### 1. `run_validation_study.py`

**Purpose**: Run the comprehensive 100-replication parameter recovery validation study.

**Usage**:
```bash
# Run with default settings (100 replications)
python scripts/run_validation_study.py

# Custom settings
python scripts/run_validation_study.py \
    --n_replications=100 \
    --n_samples=2000 \
    --n_warmup=1000 \
    --output_dir=docs/validation_results
```

**Output**:
- `validation_summary_[timestamp].txt` - Human-readable summary
- `table1_parameter_estimates_[timestamp].csv` - Table for supplementary materials
- `raw_estimates_[timestamp].npz` - Raw data for further analysis

**Runtime**: Approximately 3-8 hours for 100 replications (depending on hardware)

---

### 2. `prior_sensitivity_analysis.py`

**Purpose**: Conduct prior sensitivity analysis by comparing results across different prior specifications.

**Usage**:
```bash
python scripts/prior_sensitivity_analysis.py
```

**Tests**:
- Component effect priors: N(0, 1²), N(0, 2²), N(0, 5²)
- Heterogeneity priors: HalfNormal(1), HalfCauchy(0.5), Uniform(0,5)

**Output**: Console output with comparison tables and sensitivity assessment

**Runtime**: Approximately 30-60 minutes

---

## Requirements

All scripts require:
- Python >= 3.9
- PyMC >= 5.0
- NumPy, Pandas, ArviZ
- CNMA platform installed

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## For Publication

### Required for RSM Journal Submission:

1. **Run validation study**:
   ```bash
   python scripts/run_validation_study.py
   ```

2. **Include results**:
   - Add `table1_parameter_estimates_*.csv` to supplementary materials
   - Update `docs/VALIDATION_RESULTS_TEMPLATE.md` with actual results
   - Include convergence diagnostics

3. **Optional but recommended**:
   ```bash
   python scripts/prior_sensitivity_analysis.py
   ```
   - Demonstrates robustness to prior choice
   - Strengthens manuscript

---

## Computational Resources

### Validation Study (100 replications):
- **CPU**: Multi-core recommended (4+ cores)
- **Memory**: ~4-8 GB RAM
- **Storage**: ~100 MB for results
- **Time**: 3-8 hours

### Prior Sensitivity:
- **CPU**: Multi-core recommended
- **Memory**: ~2-4 GB RAM
- **Time**: 30-60 minutes

### Parallelization

PyMC automatically uses multiple cores for MCMC chains. For faster execution:
- Use 4+ CPU cores
- Ensure sufficient RAM per chain (~1 GB)
- Consider running on HPC if available

---

## Troubleshooting

### Out of Memory

If you encounter memory issues:
```bash
# Reduce samples
python scripts/run_validation_study.py --n_samples=1000 --n_warmup=500

# Reduce replications (not recommended for final validation)
python scripts/run_validation_study.py --n_replications=50
```

### Convergence Issues

If replications fail to converge:
- Increase warmup: `--n_warmup=2000`
- Increase samples: `--n_samples=3000`
- Check data quality

### Slow Performance

- Ensure PyMC is using compiled backend (JAX or Aesara)
- Close other applications
- Monitor CPU usage
- Consider cloud computing (AWS, Google Cloud)

---

## Contact

For issues or questions about these scripts:
- Open an issue on GitHub
- See main README.md for contact information

---

**Last Updated**: November 2025
