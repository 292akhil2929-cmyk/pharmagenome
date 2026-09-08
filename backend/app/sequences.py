"""Direct implementations of sequence composition and linear-gap pairwise alignment."""
import hashlib
import os
from collections import Counter
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/api/sequences", tags=["Sequence analysis"])
STATS_LIMIT = 100000
ALIGN_LIMIT = 1000


def normalize_sequence(raw: str, limit: int):
    lines = raw.strip().splitlines()
    if lines and lines[0].lstrip().startswith(">"):
        lines = lines[1:]
    if any(line.lstrip().startswith(">") for line in lines):
        raise ValueError("Only one FASTA record is supported. Submit each sequence separately.")
    sequence = "".join("".join(lines).split()).upper()
    if not sequence:
        raise ValueError("Enter at least one DNA base.")
    if set(sequence) - set("ACGTN"):
        raise ValueError("DNA must contain only A, C, G, T or N. RNA, gaps and other symbols are unsupported.")
    if len(sequence) > limit:
        raise ValueError(f"Normalized sequence exceeds the {limit:,}-base limit.")
    return sequence


def identity(sequence):
    return {"length": len(sequence), "sha256": hashlib.sha256(sequence.encode("ascii")).hexdigest()}


def statistics(sequence: str, k: int):
    counts = Counter(sequence)
    known = len(sequence) - counts["N"]
    total_windows = max(len(sequence) - k + 1, 0)
    kmers = Counter(sequence[i:i + k] for i in range(total_windows) if "N" not in sequence[i:i + k])
    valid_windows = sum(kmers.values())
    return {
        "input": {**identity(sequence), "sequence": sequence},
        "known_bases": known, "unknown_bases": counts["N"],
        "gc_percent": 100 * (counts["G"] + counts["C"]) / known if known else None,
        "at_percent": 100 * (counts["A"] + counts["T"]) / known if known else None,
        "composition": [{"base": b, "count": counts[b], "percent": 100 * counts[b] / len(sequence)}
                        for b in "ACGTN"],
        "kmers": {"k": k, "total_windows": total_windows, "valid_windows": valid_windows,
                  "excluded_windows": total_windows - valid_windows, "unique": len(kmers),
                  "items": [{"kmer": mer, "count": count, "frequency": count / valid_windows}
                            for mer, count in sorted(kmers.items(), key=lambda pair: (-pair[1], pair[0]))]},
    }


def align(a: str, b: str, mode: str, match: int, mismatch: int, gap: int):
    """O(n*m) time; rolling score rows and one traceback byte per cell."""
    n, m = len(a), len(b)
    width = m + 1
    trace = bytearray((n + 1) * width)
    previous = [0] * width if mode == "local" else [j * gap for j in range(width)]
    if mode == "global":
        for j in range(1, width):
            trace[j] = 3
    preview = [previous.copy()] if n <= 20 and m <= 20 else None
    best_score, best_i, best_j = 0, 0, 0
    for i in range(1, n + 1):
        current = [0 if mode == "local" else i * gap] + [0] * m
        if mode == "global":
            trace[i * width] = 2
        for j in range(1, m + 1):
            substitution = match if a[i - 1] == b[j - 1] and a[i - 1] != "N" else mismatch
            diagonal = previous[j - 1] + substitution
            up = previous[j] + gap
            left = current[j - 1] + gap
            score = max(diagonal, up, left, 0) if mode == "local" else max(diagonal, up, left)
            current[j] = score
            # Local zero terminates. Otherwise resolve ties diagonal, up, left.
            trace[i * width + j] = (0 if mode == "local" and score == 0 else
                                    1 if score == diagonal else 2 if score == up else 3)
            if mode == "local" and score > best_score:
                best_score, best_i, best_j = score, i, j
        if preview is not None:
            preview.append(current.copy())
        previous = current
    if mode == "global":
        best_score, best_i, best_j = previous[m], n, m
    i, j = best_i, best_j
    end_a, end_b = i, j
    out_a, out_b, path = [], [], [(i, j)]
    while (i or j) and trace[i * width + j]:
        direction = trace[i * width + j]
        if direction == 1:
            out_a.append(a[i - 1])
            out_b.append(b[j - 1])
            i, j = i - 1, j - 1
        elif direction == 2:
            out_a.append(a[i - 1])
            out_b.append("-")
            i -= 1
        else:
            out_a.append("-")
            out_b.append(b[j - 1])
            j -= 1
        path.append((i, j))
    aligned_a, aligned_b = "".join(reversed(out_a)), "".join(reversed(out_b))
    markers = "".join(" " if "-" in (x, y) else "?" if "N" in (x, y) else "|" if x == y else "."
                      for x, y in zip(aligned_a, aligned_b, strict=True))
    columns = len(markers)
    return {
        "input_a": {**identity(a), "sequence": a}, "input_b": {**identity(b), "sequence": b},
        "score": best_score, "aligned_a": aligned_a, "aligned_b": aligned_b, "markers": markers,
        "columns": columns, "matches": markers.count("|"), "mismatches": markers.count("."),
        "unknown_pairs": markers.count("?"), "gap_columns": markers.count(" "),
        "identity_percent": 100 * markers.count("|") / columns if columns else None,
        "range_a": [i + 1, end_a] if columns and end_a > i else None,
        "range_b": [j + 1, end_b] if columns and end_b > j else None,
        "matrix": {"scores": preview, "path": list(reversed(path)) if preview is not None else [],
                   "row_bases": a if preview is not None else "",
                   "column_bases": b if preview is not None else ""},
    }


class StatisticsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sequence: str = Field(min_length=1, max_length=200000)
    k: int = Field(default=3, ge=1, le=6, strict=True)


class AlignmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sequence_a: str = Field(min_length=1, max_length=5000)
    sequence_b: str = Field(min_length=1, max_length=5000)
    mode: Literal["global", "local"] = "global"
    match: int = Field(default=2, ge=1, le=10, strict=True)
    mismatch: int = Field(default=-1, ge=-10, le=0, strict=True)
    gap: int = Field(default=-2, ge=-10, le=-1, strict=True)


def metadata(method, parameters, limitations):
    return {"method": method, "method_version": "1.0.0", "parameters": parameters,
            "computed_at": datetime.now(UTC), "code_revision": os.getenv("VERCEL_GIT_COMMIT_SHA", "development"),
            "source": "User-submitted DNA; no reference database lookup", "limitations": limitations}


@router.post("/statistics")
def sequence_statistics(payload: StatisticsInput):
    try:
        sequence = normalize_sequence(payload.sequence, STATS_LIMIT)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    result = statistics(sequence, payload.k)
    return {**metadata("DNA composition and overlapping k-mers", {"k": payload.k}, [
        "GC and AT percentages use A/C/G/T bases as denominator; N is excluded. All-N yields null.",
        "Nucleotide percentages use the complete normalized sequence, including N.",
        "K-mers overlap, preserve the submitted strand and exclude windows containing N.",
        "Sequences are not checked against a genome or interpreted for clinical significance.",
    ]), **result}


@router.post("/align")
def sequence_alignment(payload: AlignmentInput):
    try:
        a = normalize_sequence(payload.sequence_a, ALIGN_LIMIT)
        b = normalize_sequence(payload.sequence_b, ALIGN_LIMIT)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {**metadata("Needleman–Wunsch" if payload.mode == "global" else "Smith–Waterman",
                       {"mode": payload.mode, "match": payload.match, "mismatch": payload.mismatch, "gap": payload.gap},
                       ["Linear gap penalty applies per gap base, including terminal gaps in global mode.",
                        "N pairs always use the mismatch score, including N versus N; N never proves identity.",
                        "One optimal alignment is returned. Ties prefer diagonal, up, left; local endpoints use the first maximum.",
                        "Identity is exact A/C/G/T matches divided by alignment columns, including gaps and unknown pairs.",
                        "Coordinates are 1-based inclusive in the normalized input. No positive local score returns empty alignment.",
                        "Only the submitted orientation is compared; no reverse-complement search or significance test."]),
            **align(a, b, payload.mode, payload.match, payload.mismatch, payload.gap)}
