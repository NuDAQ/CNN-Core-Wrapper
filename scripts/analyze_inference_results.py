#!/usr/bin/env python3
"""Analyze CNN wrapper simulation CSV results."""

from __future__ import annotations

import argparse
from array import array
import csv
import json
import math
from pathlib import Path
from statistics import mean, median


REQUIRED_COLUMNS = {
    "sample_id",
    "hex_out",
    "float_out",
    "label",
    "prediction",
    "correct",
    "latency_cycles",
    "latency_us",
}


def parse_int(value: str) -> int:
    value = value.strip()
    if value.lower().startswith("0x"):
        return int(value, 16)
    return int(value)


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * pct / 100.0
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (rank - low)


def stats(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "p95": None,
        }
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": mean(values),
        "median": median(values),
        "p95": percentile(values, 95),
    }


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            return []
        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise SystemExit(f"Missing required column(s): {', '.join(sorted(missing))}")
        return list(reader)


def apply_threshold(rows: list[dict[str, str]], threshold: float | None) -> list[dict[str, str]]:
    if threshold is None:
        return rows

    updated_rows: list[dict[str, str]] = []
    for row in rows:
        updated = dict(row)
        label = parse_int(updated["label"])
        prediction = 1 if float(updated["float_out"]) > threshold else 0
        updated["prediction"] = str(prediction)
        updated["correct"] = "1" if prediction == label else "0"
        updated_rows.append(updated)
    return updated_rows


def summarize(rows: list[dict[str, str]], threshold: float | None = None) -> tuple[dict[str, object], list[dict[str, str]]]:
    labels = [parse_int(row["label"]) for row in rows]
    predictions = [parse_int(row["prediction"]) for row in rows]
    correct = [parse_int(row["correct"]) for row in rows]
    floats = [float(row["float_out"]) for row in rows]
    latency_cycles = [float(row["latency_cycles"]) for row in rows]
    latency_us = [float(row["latency_us"]) for row in rows]

    total = len(rows)
    correct_count = sum(correct)
    mismatches = [row for row in rows if parse_int(row["correct"]) != 1]

    tn = sum(1 for label, pred in zip(labels, predictions) if label == 0 and pred == 0)
    fp = sum(1 for label, pred in zip(labels, predictions) if label == 0 and pred == 1)
    fn = sum(1 for label, pred in zip(labels, predictions) if label == 1 and pred == 0)
    tp = sum(1 for label, pred in zip(labels, predictions) if label == 1 and pred == 1)

    summary = {
        "num_samples": total,
        "threshold": threshold,
        "correct": correct_count,
        "incorrect": len(mismatches),
        "accuracy": (correct_count / total) if total else None,
        "confusion_matrix": {
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
        },
        "label_counts": {
            "0": labels.count(0),
            "1": labels.count(1),
        },
        "prediction_counts": {
            "0": predictions.count(0),
            "1": predictions.count(1),
        },
        "float_out": {
            "all": stats(floats),
            "label_0": stats([value for value, label in zip(floats, labels) if label == 0]),
            "label_1": stats([value for value, label in zip(floats, labels) if label == 1]),
        },
        "latency_cycles": stats(latency_cycles),
        "latency_us": stats(latency_us),
    }
    return summary, mismatches


def write_mismatches(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "sample_id",
        "hex_out",
        "float_out",
        "label",
        "prediction",
        "correct",
        "latency_cycles",
        "latency_us",
    ]
    with path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def make_plots(rows: list[dict[str, str]], out_dir: Path, threshold: float | None = None) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib is not installed; skipped plots.")
        return

    labels = [parse_int(row["label"]) for row in rows]
    predictions = [parse_int(row["prediction"]) for row in rows]
    floats = [float(row["float_out"]) for row in rows]
    latency_us = [float(row["latency_us"]) for row in rows]

    label0 = [value for value, label in zip(floats, labels) if label == 0]
    label1 = [value for value, label in zip(floats, labels) if label == 1]

    plt.figure(figsize=(8, 5))
    bins = 50
    if label0:
        plt.hist(label0, bins=bins, alpha=0.65, label="label 0")
    if label1:
        plt.hist(label1, bins=bins, alpha=0.65, label="label 1")
    plt.axvline(0.5 if threshold is None else threshold, color="black", linestyle="--", linewidth=1, label="threshold")
    plt.xlabel("float_out")
    plt.ylabel("count")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "float_out_by_label.png", dpi=160)
    plt.close()

    if latency_us:
        plt.figure(figsize=(8, 5))
        plt.hist(latency_us, bins=50)
        plt.xlabel("latency_us")
        plt.ylabel("count")
        plt.tight_layout()
        plt.savefig(out_dir / "latency_histogram.png", dpi=160)
        plt.close()

    tn = sum(1 for label, pred in zip(labels, predictions) if label == 0 and pred == 0)
    fp = sum(1 for label, pred in zip(labels, predictions) if label == 0 and pred == 1)
    fn = sum(1 for label, pred in zip(labels, predictions) if label == 1 and pred == 0)
    tp = sum(1 for label, pred in zip(labels, predictions) if label == 1 and pred == 1)

    plt.figure(figsize=(4.5, 4))
    matrix = [[tn, fp], [fn, tp]]
    plt.imshow(matrix, cmap="Blues")
    plt.xticks([0, 1], ["pred 0", "pred 1"])
    plt.yticks([0, 1], ["label 0", "label 1"])
    for y, row in enumerate(matrix):
        for x, value in enumerate(row):
            plt.text(x, y, str(value), ha="center", va="center")
    plt.colorbar(fraction=0.046, pad=0.04)
    plt.tight_layout()
    plt.savefig(out_dir / "confusion_matrix.png", dpi=160)
    plt.close()


def histogram_range(values: list[float], fallback: tuple[float, float]) -> tuple[float, float]:
    if not values:
        return fallback
    low = min(values)
    high = max(values)
    if low == high:
        pad = max(abs(low) * 0.1, 1.0)
        return low - pad, high + pad
    pad = (high - low) * 0.05
    return low - pad, high + pad


def make_root_plots(rows: list[dict[str, str]], out_dir: Path, threshold: float | None = None) -> None:
    try:
        import ROOT
    except ImportError:
        print("PyROOT is not installed; skipped ROOT plots.")
        return

    ROOT.gROOT.SetBatch(True)

    labels = [parse_int(row["label"]) for row in rows]
    predictions = [parse_int(row["prediction"]) for row in rows]
    floats = [float(row["float_out"]) for row in rows]
    latency_us = [float(row["latency_us"]) for row in rows]

    float_low, float_high = histogram_range(floats, (-1.0, 1.0))
    latency_low, latency_high = histogram_range(latency_us, (0.0, 1.0))

    root_path = out_dir / "inference_results.root"
    root_file = ROOT.TFile(str(root_path), "RECREATE")

    tree = ROOT.TTree("inference", "CNN wrapper simulation inference results")
    sample_id = array("i", [0])
    label = array("i", [0])
    prediction = array("i", [0])
    correct = array("i", [0])
    float_out = array("d", [0.0])
    latency = array("d", [0.0])
    tree.Branch("sample_id", sample_id, "sample_id/I")
    tree.Branch("label", label, "label/I")
    tree.Branch("prediction", prediction, "prediction/I")
    tree.Branch("correct", correct, "correct/I")
    tree.Branch("float_out", float_out, "float_out/D")
    tree.Branch("latency_us", latency, "latency_us/D")

    h_float_label0 = ROOT.TH1F("float_out_label0", "float_out by label;float_out;count", 60, float_low, float_high)
    h_float_label1 = ROOT.TH1F("float_out_label1", "float_out by label;float_out;count", 60, float_low, float_high)
    h_latency = ROOT.TH1F("latency_us", "latency;latency [us];count", 60, latency_low, latency_high)
    h_confusion = ROOT.TH2F("confusion_matrix", "confusion matrix;prediction;label", 2, -0.5, 1.5, 2, -0.5, 1.5)

    for row in rows:
        sample_id[0] = parse_int(row["sample_id"])
        label[0] = parse_int(row["label"])
        prediction[0] = parse_int(row["prediction"])
        correct[0] = parse_int(row["correct"])
        float_out[0] = float(row["float_out"])
        latency[0] = float(row["latency_us"])

        tree.Fill()
        h_latency.Fill(latency[0])
        h_confusion.Fill(prediction[0], label[0])
        if label[0] == 0:
            h_float_label0.Fill(float_out[0])
        elif label[0] == 1:
            h_float_label1.Fill(float_out[0])

    for hist in (h_float_label0, h_float_label1, h_latency, h_confusion):
        hist.Write()
    tree.Write()

    canvas = ROOT.TCanvas("canvas", "canvas", 900, 650)
    h_float_label0.SetLineColor(ROOT.kBlue + 1)
    h_float_label0.SetFillColorAlpha(ROOT.kBlue + 1, 0.35)
    h_float_label1.SetLineColor(ROOT.kRed + 1)
    h_float_label1.SetFillColorAlpha(ROOT.kRed + 1, 0.35)
    h_float_label0.Draw("HIST")
    h_float_label1.Draw("HIST SAME")
    threshold_line = ROOT.TLine(0.5 if threshold is None else threshold, 0.0, 0.5 if threshold is None else threshold, max(h_float_label0.GetMaximum(), h_float_label1.GetMaximum()))
    threshold_line.SetLineColor(ROOT.kBlack)
    threshold_line.SetLineStyle(2)
    threshold_line.Draw()
    legend = ROOT.TLegend(0.68, 0.72, 0.88, 0.86)
    legend.AddEntry(h_float_label0, "label 0", "f")
    legend.AddEntry(h_float_label1, "label 1", "f")
    legend.Draw()
    canvas.SaveAs(str(out_dir / "root_float_out_by_label.png"))

    h_latency.SetLineColor(ROOT.kGreen + 2)
    h_latency.SetFillColorAlpha(ROOT.kGreen + 2, 0.35)
    h_latency.Draw("HIST")
    canvas.SaveAs(str(out_dir / "root_latency_histogram.png"))

    h_confusion.Draw("COLZ TEXT")
    canvas.SaveAs(str(out_dir / "root_confusion_matrix.png"))

    root_file.Close()
    print(f"Wrote {root_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path, help="Simulation CSV from tb_stream.sv")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Directory for summary.json, mismatches.csv, and plots",
    )
    parser.add_argument(
        "--plots",
        action="store_true",
        help="Generate PNG plots if matplotlib is available",
    )
    parser.add_argument(
        "--root-plots",
        action="store_true",
        help="Generate ROOT file and PNG plots if PyROOT is available",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Recompute prediction/correct using float_out > threshold before analysis",
    )
    args = parser.parse_args()

    rows = apply_threshold(read_rows(args.csv_path), args.threshold)
    out_dir = args.out_dir or args.csv_path.with_suffix("").parent / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not rows:
        raise SystemExit(f"No rows found in {args.csv_path}")

    summary, mismatches = summarize(rows, threshold=args.threshold)

    summary_path = out_dir / "summary.json"
    mismatch_path = out_dir / "mismatches.csv"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    write_mismatches(mismatch_path, mismatches)

    if args.plots:
        make_plots(rows, out_dir, threshold=args.threshold)
    if args.root_plots:
        make_root_plots(rows, out_dir, threshold=args.threshold)

    accuracy = summary["accuracy"]
    print(f"Samples: {summary['num_samples']}")
    print(f"Accuracy: {accuracy:.4%}" if accuracy is not None else "Accuracy: n/a")
    print(f"Mismatches: {summary['incorrect']}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {mismatch_path}")


if __name__ == "__main__":
    main()
