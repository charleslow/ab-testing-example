# AB Testing Example

This repository demonstrates a minimal workflow for running an A/A test on a sample of the
[Criteo Display Advertising Challenge](https://www.kaggle.com/c/criteo-display-ad-challenge)
dataset. The example focuses on two utilities:

1. `scripts/download_criteo_sample.py` downloads a small, publicly hosted sample of the dataset.
2. `run_aa_test.py` performs a two-tailed t-test to validate that randomly assigned buckets have
   no statistically significant difference in click-through rate.

## Getting started

Create and activate a virtual environment, then install the project in editable mode. The
repository depends on [SciPy](https://scipy.org/) for the statistical test, so `pip` will fetch it
as part of the installation:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Downloading the sample dataset

Use the download helper to fetch the 10k row sample provided by the RecoHut project. The command
below stores the file under `data/raw/criteo_sample.csv` (which is ignored by git):

```bash
python scripts/download_criteo_sample.py
```

If the file already exists you can supply `--overwrite` to refresh it. A different source URL can be
provided with `--url` when needed.

## Running the A/A test

Once you have a dataset available, run the A/A test script. The following command loads the
downloaded sample and splits the observations into equal-sized buckets:

```bash
python run_aa_test.py --data-path data/raw/criteo_sample.csv
```

If you stored the sample under the default location you can omit `--data-path` entirely. Supply
`--delimiter` if your dataset uses a separator other than a comma, and `--has-header` when the
metric column is identified by name.

The script prints the mean click-through rate for both buckets, their difference, and the p-value of
a standard two-sample t-test computed via `scipy.stats.ttest_ind`. In a successful A/A test you
should expect a high p-value and a small difference between the two groups.
