"""GVR command placeholder with explicit offline limitation."""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Generate-Verify-Refine once a generator/refiner is configured.")
    parser.add_argument("--strategy", choices=["none", "random", "locate_minimum", "threshold"], default="locate_minimum")
    args = parser.parse_args()
    print({"status": "interface_ready", "strategy": args.strategy, "note": "Configure a model-backed generator and refiner before reporting GVR results."})


if __name__ == "__main__":
    main()
