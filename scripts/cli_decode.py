"""CLI for decoding a .kee metafile back into an audio file.

Usage
-----
    python -m scripts.cli_decode output.kee -o restored.wav
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.decode import decode


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Decode a .kee metafile back into an audio file."
    )
    parser.add_argument("input", help="Path to the .kee metafile")
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output audio path (default: <input_stem>_restored.wav)",
    )
    args = parser.parse_args()

    input_path = args.input
    if not os.path.isfile(input_path):
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output
    if output_path is None:
        stem = os.path.splitext(input_path)[0]
        output_path = f"{stem}_restored.wav"

    metadata = decode(input_path, output_path)

    restored_size = os.path.getsize(output_path)

    print("=== Decode complete ===")
    print(f"  Input (.kee)   : {input_path}")
    print(f"  Output (audio) : {output_path}")
    print(f"  Restored size  : {restored_size:,} bytes")
    print(f"  fs_original    : {metadata.fs_original} Hz")
    print(f"  fs_new (coded) : {metadata.fs_new} Hz")
    print(f"  D (factor)     : {metadata.downsample_factor}")
    print(f"  Channels       : {metadata.channels}")
    print(f"  Duration       : {metadata.duration:.3f} s")


if __name__ == "__main__":
    main()
