import argparse

from cheating_detector.runners.realtime import main


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FYPGuard Proctoring Pipeline")
    parser.add_argument(
        "--collect",
        action="store_true",
        help="Enable data-collection mode (saves labelled CSV)",
    )
    args = parser.parse_args()
    main(collect_mode=args.collect)
