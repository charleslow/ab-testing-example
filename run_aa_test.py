"""Run a simple A/A test using a two-tailed independent t-test from SciPy."""

from __future__ import annotations

import argparse
import csv
import pathlib
import random
import statistics
from dataclasses import dataclass
from typing import List, Optional

from scipy import stats


@dataclass
class AaTestResult:
    control_mean: float
    treatment_mean: float
    difference: float
    p_value: float
    control_size: int
    treatment_size: int


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-path",
        type=pathlib.Path,
        default=pathlib.Path("data/raw/criteo_sample.csv"),
        help="Path to the dataset file (comma-separated by default).",
    )
    parser.add_argument(
        "--metric-column",
        default="0",
        help=(
            "Column containing the binary click label. Provide either a zero-based index "
            "or a column name if the file has headers."
        ),
    )
    parser.add_argument(
        "--delimiter",
        default=",",
        help="Field delimiter used in the dataset (default: comma).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used when assigning samples to the two buckets.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.5,
        help="Proportion of observations assigned to the treatment bucket (default: 0.5).",
    )
    parser.add_argument(
        "--has-header",
        action="store_true",
        help="Treat the first row of the file as a header row.",
    )
    return parser.parse_args(argv)


def load_metric(
    data_path: pathlib.Path,
    metric_column: str,
    delimiter: str = ",",
    has_header: bool = False,
) -> List[float]:
    metric_index: Optional[int] = None
    column_name: Optional[str] = None

    if metric_column.isdigit():
        metric_index = int(metric_column)
    else:
        column_name = metric_column

    values: List[float] = []
    with data_path.open("r", newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=delimiter)
        if has_header:
            header = next(reader, None)
            if header is None:
                return values
            if column_name is not None:
                try:
                    metric_index = header.index(column_name)
                except ValueError as exc:  # pragma: no cover - defensive
                    raise ValueError(f"Column '{column_name}' not found in header") from exc
        if metric_index is None:
            raise ValueError(
                "Metric column must be a zero-based index unless --has-header is provided with a valid name."
            )
        for row in reader:
            if not row:
                continue
            try:
                values.append(float(row[metric_index]))
            except (IndexError, ValueError):
                continue
    return values


def run_aa_test(metric: List[float], seed: int = 42, test_size: float = 0.5) -> AaTestResult:
    if not 0.0 < test_size < 1.0:
        raise ValueError("test_size must be between 0 and 1")

    rng = random.Random(seed)
    treatment: List[float] = []
    control: List[float] = []
    for value in metric:
        if rng.random() < test_size:
            treatment.append(value)
        else:
            control.append(value)

    if len(control) < 2 or len(treatment) < 2:
        raise ValueError("Both groups must contain at least two observations.")

    control_mean = statistics.fmean(control)
    treatment_mean = statistics.fmean(treatment)
    difference = treatment_mean - control_mean

    _, p_value = stats.ttest_ind(control, treatment, equal_var=True, alternative="two-sided")

    return AaTestResult(
        control_mean=control_mean,
        treatment_mean=treatment_mean,
        difference=difference,
        p_value=p_value,
        control_size=len(control),
        treatment_size=len(treatment),
    )


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    metric = load_metric(
        args.data_path,
        str(args.metric_column),
        delimiter=args.delimiter,
        has_header=args.has_header,
    )
    if not metric:
        raise ValueError("No valid observations were loaded from the dataset.")

    result = run_aa_test(metric, seed=args.seed, test_size=args.test_size)

    print("Control group size:", result.control_size)
    print("Treatment group size:", result.treatment_size)
    print("Control mean CTR:", f"{result.control_mean:.4f}")
    print("Treatment mean CTR:", f"{result.treatment_mean:.4f}")
    print("Difference (treatment - control):", f"{result.difference:.4f}")
    print("Two-tailed p-value:", f"{result.p_value:.6f}")


if __name__ == "__main__":  # pragma: no cover
    main()
