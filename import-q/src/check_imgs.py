#!/usr/bin/env -S uv run --script
# coding: utf-8
# Licence: GNU AGPLv3

"""Check for duplicate or near-duplicate pictures in the BIA annales images dir."""

from __future__ import annotations

import argparse
import hashlib

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np

from PIL import Image, ImageOps

from log import SCRIPT_DIR

ANNALES_IMG_DIR = SCRIPT_DIR.parent.parent / "annales-pdf" / "sujets" / "bia-imgs"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif"}

DEFAULT_THRESHOLD = 10
DEFAULT_SSIM_THRESHOLD = 0.65
SSIM_SIZE = 128


@dataclass(frozen=True)
class Fingerprint:
    name: str
    path: Path
    dhash: int
    ahash: int
    size: tuple[int, int]

    @classmethod
    def from_image(cls, name: str, path: Path, image: Image.Image) -> "Fingerprint":
        return cls(
            name=name,
            path=path,
            dhash=_dhash(image),
            ahash=_ahash(image),
            size=image.size,
        )


def _dhash(image: Image.Image, hash_size: int = 8) -> int:
    image = image.convert("L").resize(
        (hash_size + 1, hash_size), Image.Resampling.LANCZOS
    )
    pixels = image.tobytes()
    bits = 0
    for row in range(hash_size):
        for col in range(hash_size):
            bits = (bits << 1) | int(
                pixels[row * (hash_size + 1) + col]
                > pixels[row * (hash_size + 1) + col + 1]
            )
    return bits


def _ahash(image: Image.Image, hash_size: int = 8) -> int:
    image = ImageOps.grayscale(image).resize(
        (hash_size, hash_size), Image.Resampling.LANCZOS
    )
    pixels = image.tobytes()
    avg = sum(pixels) / len(pixels)
    bits = 0
    for pixel in pixels:
        bits = (bits << 1) | int(pixel > avg)
    return bits


def _hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def _ssim(a: np.ndarray, b: np.ndarray, window: int = 8) -> float:
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    a_windows = np.lib.stride_tricks.sliding_window_view(a, (window, window))
    b_windows = np.lib.stride_tricks.sliding_window_view(b, (window, window))
    a_mean = a_windows.mean(axis=(-2, -1))
    b_mean = b_windows.mean(axis=(-2, -1))
    a_var = a_windows.var(axis=(-2, -1))
    b_var = b_windows.var(axis=(-2, -1))
    a_b_cov = (a_windows * b_windows).mean(axis=(-2, -1)) - a_mean * b_mean
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    ssim_map = ((2 * a_mean * b_mean + c1) * (2 * a_b_cov + c2)) / (
        (a_mean**2 + b_mean**2 + c1) * (a_var + b_var + c2)
    )
    return float(ssim_map.mean())


def ssim_between(a: Fingerprint, b: Fingerprint) -> float:
    a_gray = _load_gray(a.path, SSIM_SIZE)
    b_gray = _load_gray(b.path, SSIM_SIZE)
    return _ssim(a_gray, b_gray)


def _load_gray(path: Path, size: int) -> np.ndarray:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image)
        image = ImageOps.grayscale(image).resize((size, size), Image.Resampling.LANCZOS)
        return np.asarray(image, dtype=np.uint8)


def list_images(directory: Path) -> list[Path]:
    return sorted(
        p for p in directory.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS
    )


def md5_of(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def find_exact_duplicates(paths: Sequence[Path]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for path in paths:
        groups.setdefault(md5_of(path), []).append(path.name)
    return {digest: names for digest, names in groups.items() if len(names) > 1}


def load_fingerprints(paths: Sequence[Path]) -> list[Fingerprint]:
    fingerprints: list[Fingerprint] = []
    for path in paths:
        try:
            with Image.open(path) as image:
                image = ImageOps.exif_transpose(image)
                fingerprints.append(Fingerprint.from_image(path.name, path, image))
        except Exception as e:
            print(f"SKIP {path.name}: {e}")
    return fingerprints


@dataclass(frozen=True)
class SimilarPair:
    dist: int
    ssim: float
    a: Fingerprint
    b: Fingerprint


def candidate_pairs(
    fingerprints: Sequence[Fingerprint], threshold: int
) -> list[tuple[int, Fingerprint, Fingerprint]]:
    pairs: list[tuple[int, Fingerprint, Fingerprint]] = []
    for i, a in enumerate(fingerprints):
        for b in fingerprints[i + 1 :]:
            dist = min(_hamming(a.dhash, b.dhash), _hamming(a.ahash, b.ahash))
            if dist <= threshold:
                pairs.append((dist, a, b))
    return sorted(pairs, key=lambda pair: pair[0])


def similar_pairs(
    fingerprints: Sequence[Fingerprint],
    threshold: int,
    ssim_threshold: float,
    skip_same_stem: bool = True,
    verbose: bool = False,
) -> list[SimilarPair]:
    pairs: list[SimilarPair] = []
    for dist, a, b in candidate_pairs(fingerprints, threshold):
        if skip_same_stem and Path(a.name).stem == Path(b.name).stem:
            continue
        ssim = ssim_between(a, b)
        if verbose:
            print(f"  verify dist={dist:2d} ssim={ssim:.3f} {a.name} == {b.name}")
        if ssim >= ssim_threshold:
            pairs.append(SimilarPair(dist=dist, ssim=ssim, a=a, b=b))
    return sorted(pairs, key=lambda pair: pair.ssim, reverse=True)


def find_duplicate_groups(
    directory: Path,
    threshold: int = DEFAULT_THRESHOLD,
    ssim_threshold: float = DEFAULT_SSIM_THRESHOLD,
    skip_same_stem: bool = True,
    verbose: bool = False,
) -> tuple[dict[str, list[str]], list[SimilarPair]]:
    return find_duplicate_groups_from_paths(
        list_images(directory),
        threshold,
        ssim_threshold,
        skip_same_stem=skip_same_stem,
        verbose=verbose,
    )


def find_duplicate_groups_from_paths(
    paths: Sequence[Path],
    threshold: int = DEFAULT_THRESHOLD,
    ssim_threshold: float = DEFAULT_SSIM_THRESHOLD,
    skip_same_stem: bool = True,
    verbose: bool = False,
) -> tuple[dict[str, list[str]], list[SimilarPair]]:
    paths = sorted(paths)
    exact = find_exact_duplicates(paths)
    fingerprints = load_fingerprints(paths)
    pairs = similar_pairs(
        fingerprints,
        threshold,
        ssim_threshold,
        skip_same_stem=skip_same_stem,
        verbose=verbose,
    )
    return exact, pairs


def pair_key(pair: SimilarPair) -> str:
    return "|".join(sorted((pair.a.name, pair.b.name)))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check for duplicate or similar images in the BIA annales images dir"
    )
    parser.add_argument(
        "-d",
        "--dir",
        type=Path,
        default=ANNALES_IMG_DIR,
        help=f"Directory to scan (default: {ANNALES_IMG_DIR})",
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        help=f"Max Hamming distance (out of 64) to consider images similar (default: {DEFAULT_THRESHOLD})",
    )
    parser.add_argument(
        "-s",
        "--ssim-threshold",
        type=float,
        default=DEFAULT_SSIM_THRESHOLD,
        help=f"Min SSIM score (0-1) to confirm a candidate pair (default: {DEFAULT_SSIM_THRESHOLD})",
    )
    parser.add_argument(
        "--same-stem",
        action="store_true",
        default=False,
        help="Also report pairs sharing the same stem (e.g. 2017-005.png vs 2017-005.tif)",
    )
    args = parser.parse_args()

    print(f"Scanning {args.dir}\n")
    exact, pairs = find_duplicate_groups(
        args.dir,
        args.threshold,
        args.ssim_threshold,
        skip_same_stem=not args.same_stem,
        verbose=True,
    )

    if exact:
        print("=== Exact duplicates (identical bytes) ===")
        for names in exact.values():
            print("  " + " == ".join(names))
    else:
        print("=== Exact duplicates (identical bytes): none ===")
    print()

    if not pairs:
        print(
            f"=== Similar images (Hamming <= {args.threshold}, SSIM >= "
            f"{args.ssim_threshold}): none ==="
        )
        return
    print(
        f"\n=== Similar images (Hamming <= {args.threshold}, SSIM >= "
        f"{args.ssim_threshold}) ==="
    )
    for pair in pairs:
        print(
            f"  ssim={pair.ssim:.3f} dist={pair.dist:2d} {pair.a.size} "
            f"{pair.a.name} == {pair.b.size} {pair.b.name}"
        )


########
# Main #
########

if __name__ == "__main__":
    print("#" * 80)
    main()
