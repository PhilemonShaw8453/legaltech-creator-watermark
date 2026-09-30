import argparse
from datetime import date
from pathlib import Path

from legal_image_service import InfraiClient, MatterIntake, publish_creator_image


def main() -> None:
    parser = argparse.ArgumentParser(description="Watermark a legal-tech creator image before publishing")
    parser.add_argument("image", type=Path)
    parser.add_argument("--matter", required=True)
    parser.add_argument("--creator", required=True)
    parser.add_argument("--deadline", required=True, help="ISO date, for example 2026-10-01")
    args = parser.parse_args()
    matter = MatterIntake(args.matter, args.creator, date.fromisoformat(args.deadline))
    print(publish_creator_image(InfraiClient(), matter, args.image))


if __name__ == "__main__":
    main()
