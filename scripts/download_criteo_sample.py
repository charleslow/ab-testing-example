"""Download a small sample of the public Criteo click-through-rate dataset.

The script defaults to the sample hosted by the RecoHut AB testing tutorial project on GitHub.
The file contains the first 10,000 rows of the original Kaggle dataset and is more than
sufficient for demonstration purposes.

Example usage
-------------
python scripts/download_criteo_sample.py \
    --output data/raw/criteo_sample.csv
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
from typing import Optional
from urllib.request import urlopen

DEFAULT_URL = (
    "https://github.com/RecoHut-Projects/AB-Testing-Tutorial/raw/main/data/criteo_sampled_data.csv"
)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="Location of the sample dataset to download.",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=pathlib.Path("data/raw/criteo_sample.csv"),
        help="Where to store the downloaded file.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the existing file if it already exists.",
    )
    return parser.parse_args(argv)


def download(url: str, destination: pathlib.Path, overwrite: bool = False) -> pathlib.Path:
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and not overwrite:
        raise FileExistsError(
            f"Destination '{destination}' already exists. Use --overwrite to replace it."
        )

    with urlopen(url) as response, destination.open("wb") as file:  # type: ignore[arg-type]
        shutil.copyfileobj(response, file)
    return destination


def main(argv: Optional[list[str]] = None) -> None:
    args = parse_args(argv)
    path = download(args.url, args.output, args.overwrite)
    print(f"Downloaded sample dataset to {path}")


if __name__ == "__main__":  # pragma: no cover
    main()
