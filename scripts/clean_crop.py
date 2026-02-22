#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove bottom/right watermark area by cropping from top-left, then resample back.",
    )
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", help="Output image path")
    parser.add_argument(
        "--crop-width",
        type=int,
        default=2000,
        help="Crop width (default: 2000). Keep 4:3 ratio with crop-height.",
    )
    parser.add_argument(
        "--crop-height",
        type=int,
        default=1500,
        help="Crop height (default: 1500). Keep 4:3 ratio with crop-width.",
    )
    parser.add_argument(
        "--out-width",
        type=int,
        default=2304,
        help="Resample width (default: 2304).",
    )
    parser.add_argument(
        "--out-height",
        type=int,
        default=1728,
        help="Resample height (default: 1728).",
    )
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = out_path.with_suffix(".tmp" + out_path.suffix)
    if tmp_path.exists():
        tmp_path.unlink()

    _run(
        [
            "sips",
            "--cropToHeightWidth",
            str(args.crop_height),
            str(args.crop_width),
            "--cropOffset",
            "0",
            "0",
            str(in_path),
            "--out",
            str(tmp_path),
        ]
    )
    _run(
        [
            "sips",
            "--resampleHeightWidth",
            str(args.out_height),
            str(args.out_width),
            str(tmp_path),
            "--out",
            str(out_path),
        ]
    )
    try:
        tmp_path.unlink(missing_ok=True)
    except Exception:
        pass

    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

