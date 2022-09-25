from _transfer import DataTransfer
import argparse

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", required=True, help="Output folder")
ap.add_argument(
    "-d",
    "--directories",
    nargs="+",
    help="Directories to clean",
    required=True,
)

args = ap.parse_args()

# Transfer all
for f in args.directories:
    DataTransfer(f, args.output).transfer()
