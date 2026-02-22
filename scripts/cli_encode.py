"""CLI for encoding an audio file into a .kee metafile.

Usage
-----
    python -m scripts.cli_encode input.wav -o output.kee
    python -m scripts.cli_encode input.wav -o output.kee -d 4
    python -m scripts.cli_encode input.wav -o output.kee --threshold 300
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.encode import encode


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Encode an audio file into a .kee metafile."
    )
    parser.add_argument("input", help="Path to the input audio file (e.g. WAV)")
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output .kee path (default: <input_stem>.kee)",
    )
    parser.add_argument(
        "-d", "--downsample-factor", type=int, default=None,
        help="Downsample factor D (omit for FFT-based auto computation)",
    )
    parser.add_argument(
        "--threshold", type=float, default=500.0,
        help="Amplitude threshold for auto-D computation (default: 500)",
    )
    args = parser.parse_args()

    input_path = args.input
    if not os.path.isfile(input_path):
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output
    if output_path is None:
        stem = os.path.splitext(input_path)[0]
        output_path = f"{stem}.kee"

    original_size = os.path.getsize(input_path)

    metadata = encode(input_path, output_path, args.downsample_factor, args.threshold)

    compressed_size = os.path.getsize(output_path)
    ratio = original_size / compressed_size if compressed_size > 0 else float("inf")

    print("=== Encode complete ===")
    print(f"  Input          : {input_path}")
    print(f"  Output         : {output_path}")
    print(f"  Original size  : {original_size:,} bytes")
    print(f"  Compressed size: {compressed_size:,} bytes")
    print(f"  Ratio          : {ratio:.2f}x")
    print(f"  fs_original    : {metadata.fs_original} Hz")
    print(f"  fs_new         : {metadata.fs_new} Hz")
    print(f"  D (factor)     : {metadata.downsample_factor}")
    print(f"  Channels       : {metadata.channels}")
    print(f"  Duration       : {metadata.duration:.3f} s")


if __name__ == "__main__":
    main()
