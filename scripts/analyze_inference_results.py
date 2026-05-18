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


DEFAULT_KERAS_MODEL = Path("/home/work1/Works/CNN-Core-Generator/models/hgq_config_beta7_gamma6_p1_cl_best_v3.keras")
DEFAULT_X_TEST = Path("/home/work1/Works/CNN-Core-Generator/data/X_test_data.npy")
DEFAULT_Y_TEST = Path("/home/work1/Works/CNN-Core-Generator/data/y_test_labels.npy")

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


def confusion_summary(labels: list[int], predictions: list[int]) -> dict[str, object]:
    tn = sum(1 for label, pred in zip(labels, predictions) if label == 0 and pred == 0)
    fp = sum(1 for label, pred in zip(labels, predictions) if label == 0 and pred == 1)
    fn = sum(1 for label, pred in zip(labels, predictions) if label == 1 and pred == 0)
    tp = sum(1 for label, pred in zip(labels, predictions) if label == 1 and pred == 1)
    total = len(labels)
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    specificity = tn / (tn + fp) if (tn + fp) else None
    f1 = (2 * precision * recall / (precision + recall)) if precision is not None and recall is not None and (precision + recall) else None
    return {
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
        "accuracy": ((tn + tp) / total) if total else None,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1,
    }


def threshold_metrics(labels: list[int], scores: list[float], threshold: float) -> dict[str, object]:
    predictions = [1 if score > threshold else 0 for score in scores]
    return {"threshold": threshold, **confusion_summary(labels, predictions)}


def best_threshold_summary(labels: list[int], scores: list[float]) -> dict[str, object] | None:
    if not labels or not scores or len(labels) != len(scores):
        return None
    values = sorted(set(scores))
    if not values:
        return None
    thresholds = [values[0] - 1.0] + [(left + right) / 2.0 for left, right in zip(values, values[1:])] + [values[-1] + 1.0]
    return max((threshold_metrics(labels, scores, threshold) for threshold in thresholds), key=lambda item: item["accuracy"] or 0.0)


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

    confusion = confusion_summary(labels, predictions)

    summary = {
        "num_samples": total,
        "threshold": threshold,
        "correct": correct_count,
        "incorrect": len(mismatches),
        "accuracy": (correct_count / total) if total else None,
        "confusion_matrix": {
            "tn": confusion["tn"],
            "fp": confusion["fp"],
            "fn": confusion["fn"],
            "tp": confusion["tp"],
        },
        "metrics": {
            "precision": confusion["precision"],
            "recall": confusion["recall"],
            "specificity": confusion["specificity"],
            "f1": confusion["f1"],
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


def write_comparison(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    fieldnames = [
        "sample_id",
        "label_csv",
        "label_npy",
        "rtl_score",
        "rtl_prediction",
        "rtl_correct",
        "keras_score",
        "keras_prediction",
        "keras_correct",
        "prediction_agree",
        "both_correct",
        "score_diff",
        "abs_score_diff",
    ]
    with path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def finite_correlation(left: list[float], right: list[float]) -> float | None:
    if len(left) < 2 or len(right) < 2 or len(left) != len(right):
        return None
    mean_left = mean(left)
    mean_right = mean(right)
    num = sum((a - mean_left) * (b - mean_right) for a, b in zip(left, right))
    den_left = math.sqrt(sum((a - mean_left) ** 2 for a in left))
    den_right = math.sqrt(sum((b - mean_right) ** 2 for b in right))
    if den_left == 0 or den_right == 0:
        return None
    return num / (den_left * den_right)


def load_keras_model(path: Path):
    try:
        from tensorflow import keras
    except ImportError:
        try:
            import keras
        except ImportError as exc:
            raise SystemExit("TensorFlow/Keras is required for default model comparison.") from exc

    try:
        import hgq  # noqa: F401
        from hgq.layers import QConv2D, QDense
    except ImportError as exc:
        raise SystemExit(
            "HGQ is required to load the default .keras model. "
            "Install it in the active venv, for example: python -m pip install hgq"
        ) from exc

    custom_objects = {
        "QConv2D": QConv2D,
        "QDense": QDense,
        "hgq>QConv2D": QConv2D,
        "hgq>QDense": QDense,
    }
    try:
        from hgq.constraints import MinMax
        custom_objects.update({"MinMax": MinMax, "hgq>MinMax": MinMax})
    except ImportError:
        pass
    try:
        from hgq.regularizers import MonoL1
        custom_objects.update({"MonoL1": MonoL1, "hgq>MonoL1": MonoL1})
    except ImportError:
        pass
    try:
        from hgq.quantizer.config import QuantizerConfig
        custom_objects.update({"QuantizerConfig": QuantizerConfig, "hgq>QuantizerConfig": QuantizerConfig})
    except ImportError:
        pass

    load_kwargs = {"custom_objects": custom_objects, "compile": False}
    try:
        return keras.models.load_model(path, safe_mode=False, **load_kwargs)
    except TypeError:
        return keras.models.load_model(path, **load_kwargs)


def flatten_binary_outputs(predictions) -> list[float]:
    import numpy as np

    array_values = np.asarray(predictions)
    if array_values.ndim == 1:
        return [float(value) for value in array_values]
    if array_values.ndim == 2 and array_values.shape[1] == 1:
        return [float(value) for value in array_values[:, 0]]
    if array_values.ndim >= 2 and array_values.shape[-1] == 1:
        return [float(value) for value in array_values.reshape((array_values.shape[0], -1))[:, 0]]
    if array_values.ndim >= 2 and array_values.shape[-1] > 1:
        return [float(value) for value in array_values.reshape((array_values.shape[0], -1))[:, -1]]
    return [float(value) for value in array_values.reshape(-1)]


def flatten_labels(labels) -> list[int]:
    import numpy as np

    array_values = np.asarray(labels)
    if array_values.ndim == 1:
        return [int(round(float(value))) for value in array_values]
    if array_values.ndim >= 2 and array_values.shape[-1] == 1:
        return [int(round(float(value))) for value in array_values.reshape((array_values.shape[0], -1))[:, 0]]
    if array_values.ndim >= 2 and array_values.shape[-1] > 1:
        return [int(value) for value in np.argmax(array_values.reshape((array_values.shape[0], -1)), axis=1)]
    return [int(round(float(value))) for value in array_values.reshape(-1)]


def prepare_model_input(model, x_test):
    import numpy as np

    input_shape = model.input_shape
    if isinstance(input_shape, list):
        input_shape = input_shape[0]
    target_shape = tuple(dim for dim in input_shape[1:] if dim is not None)

    if tuple(x_test.shape[1:]) == target_shape:
        return x_test, "as_loaded"

    if len(target_shape) == 2 and x_test.ndim == 4 and x_test.shape[-1] == 1:
        squeezed = x_test[..., 0]
        if tuple(squeezed.shape[1:]) == target_shape:
            return squeezed, "squeeze_last_axis"
        transposed = np.transpose(squeezed, (0, 2, 1))
        if tuple(transposed.shape[1:]) == target_shape:
            return transposed, "transpose_from_channels_first_time_series"

    raise SystemExit(
        f"Could not reshape X_test from {tuple(x_test.shape)} to model input shape {input_shape}."
    )


def compare_with_keras(rows: list[dict[str, str]], threshold: float | None) -> tuple[dict[str, object] | None, list[dict[str, object]]]:
    if not (DEFAULT_KERAS_MODEL.exists() and DEFAULT_X_TEST.exists() and DEFAULT_Y_TEST.exists()):
        print("Keras comparison inputs were not found; skipped default model comparison.")
        return None, []

    import numpy as np

    x_test_raw = np.load(DEFAULT_X_TEST)
    y_test = flatten_labels(np.load(DEFAULT_Y_TEST))
    model = load_keras_model(DEFAULT_KERAS_MODEL)
    x_test, input_transform = prepare_model_input(model, x_test_raw)
    keras_scores = flatten_binary_outputs(model.predict(x_test, verbose=0))

    if not keras_scores:
        raise SystemExit("Keras model produced no predictions.")

    score_min = min(keras_scores)
    score_max = max(keras_scores)
    keras_threshold = 0.5

    comparison_rows: list[dict[str, object]] = []
    rtl_scores: list[float] = []
    matched_keras_scores: list[float] = []
    labels: list[int] = []
    rtl_predictions: list[int] = []
    keras_predictions: list[int] = []
    score_diffs: list[float] = []
    abs_score_diffs: list[float] = []
    label_mismatches = 0

    for row in rows:
        sample_id = parse_int(row["sample_id"])
        if sample_id >= len(keras_scores) or sample_id >= len(y_test):
            continue

        label_csv = parse_int(row["label"])
        label_npy = y_test[sample_id]
        if label_csv != label_npy:
            label_mismatches += 1

        rtl_score = float(row["float_out"])
        rtl_prediction = parse_int(row["prediction"])
        keras_score = keras_scores[sample_id]
        keras_prediction = 1 if keras_score > keras_threshold else 0
        keras_correct = 1 if keras_prediction == label_npy else 0
        rtl_correct = parse_int(row["correct"])
        score_diff = rtl_score - keras_score
        abs_score_diff = abs(score_diff)

        rtl_scores.append(rtl_score)
        matched_keras_scores.append(keras_score)
        labels.append(label_npy)
        rtl_predictions.append(rtl_prediction)
        keras_predictions.append(keras_prediction)
        score_diffs.append(score_diff)
        abs_score_diffs.append(abs_score_diff)

        comparison_rows.append(
            {
                "sample_id": sample_id,
                "label_csv": label_csv,
                "label_npy": label_npy,
                "rtl_score": rtl_score,
                "rtl_prediction": rtl_prediction,
                "rtl_correct": rtl_correct,
                "keras_score": keras_score,
                "keras_prediction": keras_prediction,
                "keras_correct": keras_correct,
                "prediction_agree": 1 if rtl_prediction == keras_prediction else 0,
                "both_correct": 1 if rtl_correct and keras_correct else 0,
                "score_diff": score_diff,
                "abs_score_diff": abs_score_diff,
            }
        )

    if not comparison_rows:
        raise SystemExit("No overlapping sample IDs between RTL CSV and Keras predictions.")

    keras_confusion = confusion_summary(labels, keras_predictions)
    rtl_confusion = confusion_summary(labels, rtl_predictions)
    prediction_agreements = sum(1 for left, right in zip(rtl_predictions, keras_predictions) if left == right)
    agreement = prediction_agreements / len(comparison_rows)
    conversion_summary = {
        "model_path": str(DEFAULT_KERAS_MODEL),
        "x_test_path": str(DEFAULT_X_TEST),
        "y_test_path": str(DEFAULT_Y_TEST),
        "x_test_shape_raw": list(x_test_raw.shape),
        "x_test_shape_model": list(x_test.shape),
        "x_test_transform": input_transform,
        "num_compared": len(comparison_rows),
        "label_mismatches_between_csv_and_npy": label_mismatches,
        "keras_threshold": keras_threshold,
        "rtl_threshold": threshold,
        "keras_score": stats(matched_keras_scores),
        "rtl_score": stats(rtl_scores),
        "score_diff_rtl_minus_keras": {
            **stats(score_diffs),
            "mae": mean(abs_score_diffs),
            "rmse": math.sqrt(mean([value * value for value in score_diffs])),
            "max_abs": max(abs_score_diffs),
            "correlation": finite_correlation(rtl_scores, matched_keras_scores),
        },
        "keras_metrics": keras_confusion,
        "rtl_metrics_on_npy_labels": rtl_confusion,
        "keras_default_threshold": threshold_metrics(labels, matched_keras_scores, 0.5),
        "keras_best_threshold": best_threshold_summary(labels, matched_keras_scores),
        "rtl_best_threshold": best_threshold_summary(labels, rtl_scores),
        "prediction_agreement": agreement,
        "prediction_disagreements": len(comparison_rows) - prediction_agreements,
    }
    return conversion_summary, comparison_rows


def make_plots(
    rows: list[dict[str, str]],
    out_dir: Path,
    threshold: float | None = None,
    comparison_rows: list[dict[str, object]] | None = None,
) -> None:
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
    plt.yscale("log")
    plt.xlabel("float_out")
    plt.ylabel("count")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "float_out_by_label.png", dpi=160)
    plt.close()

    if latency_us:
        plt.figure(figsize=(8, 5))
        plt.hist(latency_us, bins=50)
        plt.yscale("log")
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

    if comparison_rows:
        rtl_scores = [float(row["rtl_score"]) for row in comparison_rows]
        keras_scores = [float(row["keras_score"]) for row in comparison_rows]
        score_diffs = [float(row["score_diff"]) for row in comparison_rows]

        plt.figure(figsize=(6, 6))
        plt.scatter(keras_scores, rtl_scores, s=10, alpha=0.65)
        plt.xlabel("Keras score")
        plt.ylabel("RTL score")
        plt.tight_layout()
        plt.savefig(out_dir / "keras_vs_rtl_score.png", dpi=160)
        plt.close()

        plt.figure(figsize=(8, 5))
        plt.hist(score_diffs, bins=60)
        plt.yscale("log")
        plt.xlabel("RTL score - Keras score")
        plt.ylabel("count")
        plt.tight_layout()
        plt.savefig(out_dir / "conversion_score_diff_histogram.png", dpi=160)
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


def make_root_plots(
    rows: list[dict[str, str]],
    out_dir: Path,
    threshold: float | None = None,
    comparison_rows: list[dict[str, object]] | None = None,
) -> None:
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
    h_score_diff = None
    h_score_scatter = None
    if comparison_rows:
        score_diffs = [float(row["score_diff"]) for row in comparison_rows]
        rtl_scores = [float(row["rtl_score"]) for row in comparison_rows]
        keras_scores = [float(row["keras_score"]) for row in comparison_rows]
        diff_low, diff_high = histogram_range(score_diffs, (-1.0, 1.0))
        rtl_low, rtl_high = histogram_range(rtl_scores, (-1.0, 1.0))
        keras_low, keras_high = histogram_range(keras_scores, (-1.0, 1.0))
        h_score_diff = ROOT.TH1F("score_diff_rtl_minus_keras", "conversion score difference;RTL score - Keras score;count", 80, diff_low, diff_high)
        h_score_scatter = ROOT.TH2F("keras_vs_rtl_score", "Keras vs RTL score;Keras score;RTL score", 80, keras_low, keras_high, 80, rtl_low, rtl_high)

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

    if comparison_rows:
        for row in comparison_rows:
            h_score_diff.Fill(float(row["score_diff"]))
            h_score_scatter.Fill(float(row["keras_score"]), float(row["rtl_score"]))

    for hist in (h_float_label0, h_float_label1, h_latency, h_confusion, h_score_diff, h_score_scatter):
        if hist is None:
            continue
        hist.Write()
    tree.Write()

    canvas = ROOT.TCanvas("canvas", "canvas", 900, 650)
    canvas.SetLogy(True)
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
    canvas.SetLogy(True)
    h_latency.Draw("HIST")
    canvas.SaveAs(str(out_dir / "root_latency_histogram.png"))

    canvas.SetLogy(False)
    h_confusion.Draw("COLZ TEXT")
    canvas.SaveAs(str(out_dir / "root_confusion_matrix.png"))

    if h_score_diff is not None and h_score_scatter is not None:
        h_score_diff.SetLineColor(ROOT.kMagenta + 2)
        h_score_diff.SetFillColorAlpha(ROOT.kMagenta + 2, 0.35)
        canvas.SetLogy(True)
        h_score_diff.Draw("HIST")
        canvas.SaveAs(str(out_dir / "root_conversion_score_diff_histogram.png"))

        canvas.SetLogy(False)
        h_score_scatter.Draw("COLZ")
        canvas.SaveAs(str(out_dir / "root_keras_vs_rtl_score.png"))

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
    conversion_summary, comparison_rows = compare_with_keras(rows, threshold=args.threshold)
    if conversion_summary is not None:
        summary["keras_comparison"] = conversion_summary

    summary_path = out_dir / "summary.json"
    mismatch_path = out_dir / "mismatches.csv"
    comparison_path = out_dir / "keras_comparison.csv"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    write_mismatches(mismatch_path, mismatches)
    write_comparison(comparison_path, comparison_rows)

    if args.plots:
        make_plots(rows, out_dir, threshold=args.threshold, comparison_rows=comparison_rows)
    if args.root_plots:
        make_root_plots(rows, out_dir, threshold=args.threshold, comparison_rows=comparison_rows)

    accuracy = summary["accuracy"]
    print(f"Samples: {summary['num_samples']}")
    print(f"Accuracy: {accuracy:.4%}" if accuracy is not None else "Accuracy: n/a")
    print(f"Mismatches: {summary['incorrect']}")
    if conversion_summary is not None:
        keras_accuracy = conversion_summary["keras_metrics"]["accuracy"]
        print(f"Keras accuracy: {keras_accuracy:.4%}" if keras_accuracy is not None else "Keras accuracy: n/a")
        print(f"RTL/Keras prediction agreement: {conversion_summary['prediction_agreement']:.4%}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {mismatch_path}")
    if comparison_rows:
        print(f"Wrote {comparison_path}")


if __name__ == "__main__":
    main()
