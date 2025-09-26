# AA Testing Example

Run repeated A/A tests on the provided dataset.

The aim is to demonstrate the danger of mismatched assignment and analysis levels.

The script assigns treatment at the `user_id` level, but analyses the results at three different levels: row, `impression_id`, and `user_id`.

Each trial randomly assigns users to control or treatment using a hash function with a trial-specific salt. This ensures that treatment assignment is independent across trials.

The click-through rate (CTR) is computed for each group at the specified analysis level. Since this is an A/A test, we expect no difference in CTR between control and treatment groups. A significant p-value indicates a false positive.

We expect the false positive rate to be close to the significance level (`alpha`) when the assignment and analysis levels match (`user_id`). However, when they do not match (row or `impression_id`), the false positive rate may be higher than expected.

## Getting started

Create and activate a virtual environment, then install the project in editable mode.

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Running the A/A test

```bash
uv run python run_aa_test.py --trials 100 --alpha 0.05
```

The script performs the AA test at the row, impression and user level. Note that it uses the `criteo/FairJob` dataset for the analysis, although the findings from this analysis applies to any dataset where the experiment assignment differs from the level of AB analysis. We expect the false positive rate for the user level to be close to the alpha, but the other levels to be higher.

## Output

```bash
>>> uv run python run_aa_test.py --trials 1000 --alpha 0.05
=== A/A Test Summary ===
Level: row
Trials: 1000
Alpha: 0.05
False positives: 614 (61.40%)
=== A/A Test Summary ===
Level: impression_id
Trials: 1000
Alpha: 0.05
False positives: 324 (32.40%)
=== A/A Test Summary ===
Level: user_id
Trials: 1000
Alpha: 0.05
False positives: 56 (5.60%)
```
