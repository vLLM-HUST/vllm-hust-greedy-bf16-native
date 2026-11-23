# SPDX-License-Identifier: Apache-2.0
"""Build the exact experimental sampler overlay from an admitted R10 source file."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]


def verify_digest(data, expected, label):
    observed = sha256(data).hexdigest()
    if observed != expected:
        raise ValueError(f"{label} SHA-256 mismatch: {observed}")


def build(source: Path, output: Path):
    manifest = json.loads((ROOT / "mod.json").read_bytes())
    patch = ROOT / manifest["patch"]
    original = source.read_bytes()
    verify_digest(original, manifest["original_sha256"], "Frozen sampler")
    verify_digest(patch.read_bytes(), manifest["patch_sha256"], "Patch")

    with TemporaryDirectory(dir=output.parent) as folder:
        working = Path(folder) / "rejection_sampler.py"
        working.write_bytes(original)
        subprocess.run(
            ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "apply", "--no-index", "-p1", str(patch)],
            cwd=folder,
            check=True,
            capture_output=True,
        )
        result = working.read_bytes()
        verify_digest(result, manifest["candidate_sha256"], "Built overlay")
        compile(result, output.name, "exec")
        with output.open("xb") as stream:
            stream.write(result)
    return manifest["candidate_sha256"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Exact R10 rejection_sampler.py")
    parser.add_argument("output", type=Path, help="Fresh overlay file in a separate directory")
    args = parser.parse_args()
    try:
        digest = build(args.source, args.output)
    except subprocess.CalledProcessError as exc:
        parser.exit(1, f"Git could not apply the sealed patch: {exc.stderr.decode(errors='replace')}\n")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")
    print(f"{digest}  {args.output}")


if __name__ == "__main__":
    main()