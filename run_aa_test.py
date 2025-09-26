"""Run repeated A/A tests on the provided dataset.

The aim is to demonstrate the danger of mismatched assignment and analysis levels.

The script assigns treatment at the user_id level, but analyses the results at three different
levels: row, impression_id, and user_id.

Each trial randomly assigns users to control or treatment using a hash function with a trial-specific
salt. This ensures that treatment assignment is independent across trials.

The click-through rate (CTR) is computed for each group at the specified analysis level. Since
this is an A/A test, we expect no difference in CTR between control and treatment groups.
A significant p-value indicates a false positive.

We expect the false positive rate to be close to the significance level (alpha) when
the assignment and analysis levels match (user_id). However, when they do not match (row or impression_id),
the false positive rate may be inflated.
"""

from __future__ import annotations

import argparse
import statistics
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional

import pandas as pd
import xxhash
from datasets import load_dataset
from scipy import stats


@dataclass
class AaTestResult:
    control_mean: float
    treatment_mean: float
    p_value: float
    control_size: int
    treatment_size: int
    control_std: float
    treatment_std: float


def t_test(control: Iterable[float], treatment: Iterable[float]) -> AaTestResult:
    control_list = list(control)
    treatment_list = list(treatment)
    control_mean = statistics.fmean(control_list)
    treatment_mean = statistics.fmean(treatment_list)
    _, p_value = stats.ttest_ind(
        control_list, treatment_list, equal_var=True, alternative="two-sided"
    )
    control_std = statistics.stdev(control_list)
    treatment_std = statistics.stdev(treatment_list)
    return AaTestResult(
        control_mean=control_mean,
        treatment_mean=treatment_mean,
        p_value=p_value,
        control_size=len(control_list),
        treatment_size=len(treatment_list),
        control_std=control_std,
        treatment_std=treatment_std,
    )


def _hash_to_bucket(value: str) -> int:
    """Return 0 or 1 from hashing the provided string with xxhash64."""
    return xxhash.xxh64(value).intdigest() % 2


def compute_group_level_ctr(df: pd.DataFrame, group: str):
    """Compute per-(group, treatment) CTR.

    Validation:
      * Requires columns: group, treatment, click.
      * Raises ValueError if any group key maps to BOTH treatment=True and treatment=False
        (i.e., inconsistent assignment relative to the randomisation unit).
    """
    required_cols = {group, "treatment", "click"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame missing required columns: {missing}")

    # Aggregate clicks and counts for each (group, treatment) pair
    agg = df.groupby([group, "treatment"], as_index=False)["click"].agg(
        click_sum="sum", count="count"
    )

    # Identify groups that have both treatment True & False assignments (inconsistent assignment)
    treatment_counts = agg.groupby(group)["treatment"].nunique()
    invalid_groups = treatment_counts[treatment_counts > 1].index
    if len(invalid_groups) > 0:
        raise ValueError(
            "Found groups with inconsistent treatment assignment (group appears in both arms): "
            f"{invalid_groups.tolist()}"
        )

    # Compute CTR
    agg["ctr"] = agg["click_sum"] / agg["count"]
    return agg[[group, "treatment", "ctr", "count"]]


def assign_control_treatment(df: pd.DataFrame, level: str, suffix: str) -> pd.DataFrame:
    if level not in df.columns:
        raise ValueError(f"Level column '{level}' not found in DataFrame.")

    unique_ids = df[level].astype(str).unique()
    id_to_bucket = {uid: _hash_to_bucket(f"{uid}_{suffix}") for uid in unique_ids}
    df["bucket"] = df[level].astype(str).map(id_to_bucket)
    df["treatment"] = df["bucket"] == 1
    return df


def run_trials(
    df: pd.DataFrame,
    level: str,
    trials: int,
    alpha: float,
) -> None:
    false_positives = 0
    p_values: List[float] = []

    for trial_index in range(trials):
        # Re-assign treatment at user level with trial-specific salt so hash differs each attempt
        assigned_df = assign_control_treatment(df.copy(), level="user_id", suffix=str(trial_index))

        # Aggregate to group level CTRs
        group_ctr_df = compute_group_level_ctr(assigned_df, group=level)

        control = group_ctr_df.loc[~group_ctr_df["treatment"], "ctr"].tolist()
        treatment = group_ctr_df.loc[group_ctr_df["treatment"], "ctr"].tolist()

        result = t_test(control, treatment)
        p_values.append(result.p_value)
        if result.p_value < alpha:
            false_positives += 1

    print("=== A/A Test Summary ===")
    print(f"Level: {level}")
    print(f"Trials: {trials}")
    print(f"Alpha: {alpha}")
    fp_rate = (false_positives / trials * 100.0) if trials > 0 else float("nan")
    print(f"False positives: {false_positives} ({fp_rate:.2f}%)")


def parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run repeated A/A tests.")
    parser.add_argument("--trials", type=int, default=100, help="Number of valid trials to run.")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance threshold.")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode with a smaller dataset.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)

    ds = load_dataset("criteo/FairJob", split="train")
    df = ds.to_pandas()
    if args.debug:
        df = df.head(10_000)
    df["row"] = df.index

    for level in ["row", "impression_id", "user_id"]:
        run_trials(
            df=df,
            level=level,
            trials=args.trials,
            alpha=args.alpha,
        )


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
