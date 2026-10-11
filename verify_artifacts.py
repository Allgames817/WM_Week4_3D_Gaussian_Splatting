"""Audit this results package without training or GPU dependencies.

Python 3.10+: python verify_artifacts.py
With NumPy:  python verify_artifacts.py --recompute-metrics
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8-sig"))


def archive_check(errors):
    entries = read_json("results/source_manifest.json")["copied_files"]
    seen = set()
    for item in entries:
        relative = item["destination"]
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT) or relative in seen:
            errors.append(f"Invalid or duplicate archive destination: {relative}")
            continue
        seen.add(relative)
        if not path.is_file():
            errors.append(f"Missing artifact: {relative}")
            continue
        payload = path.read_bytes()
        if len(payload) != item["bytes"] or hashlib.sha256(payload).hexdigest() != item["sha256"]:
            errors.append(f"Artifact identity mismatch: {relative}")
    return {"copied_files_checked": len(entries)}


def document_check(errors):
    counts = {"markdown_files": 0, "html_files": 0, "local_links": 0}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts or path.suffix not in (".md", ".html"):
            continue
        content = path.read_text(encoding="utf-8-sig")
        if path.suffix == ".md":
            counts["markdown_files"] += 1
            content = re.sub(r"```.*?```", "", content, flags=re.S)
            targets = re.findall(r"\[[^\]]*\]\(([^)]+)\)", content)
        else:
            counts["html_files"] += 1
            targets = []
        targets += re.findall(r'''(?:src|href)=["']([^"']+)["']''', content)
        for target in targets:
            parsed = urlsplit(target.strip("<>"))
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            counts["local_links"] += 1
            dest = (path.parent / unquote(parsed.path)).resolve()
            if not dest.is_relative_to(ROOT) or not dest.exists():
                errors.append(f"Broken local link in {path.relative_to(ROOT)}: {target}")
    return counts


def package_check(errors):
    count, size, largest = 0, 0, (0, "")
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        length = path.stat().st_size
        count += 1
        size += length
        largest = max(largest, (length, path.relative_to(ROOT).as_posix()))
        if length >= 50 * 1024**2:
            errors.append(f"Unexpected file of 50 MiB or more: {path.relative_to(ROOT)}")
        if path.suffix.lower() in (".pt", ".pth", ".ckpt"):
            errors.append(f"Unexpected checkpoint in showcase: {path.relative_to(ROOT)}")
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8-sig"))
            except (ValueError, UnicodeError) as exc:
                errors.append(f"Invalid JSON: {path.relative_to(ROOT)}: {exc}")
    return {"files": count, "bytes": size, "largest_file": largest[1], "largest_file_bytes": largest[0]}


def numeric_close(actual, expected):
    if actual is None or expected is None:
        return actual is None and expected is None
    return math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-12)


def recompute_metrics(errors):
    import numpy as np

    with np.load(ROOT / "results/dataset/scene.npz", allow_pickle=False) as data:
        targets = data["targets"].astype(np.float64)
        backgrounds = data["backgrounds"].astype(np.float64)
        split_ids = {split: data[f"{split}_ids"].copy() for split in ("train", "val")}
    expected_ids = {"train": [0, 2, 3, 4, 6], "val": [1, 5]}
    if targets.shape != (7, 64, 96, 3) or backgrounds.shape != (7, 3):
        raise ValueError("Unexpected dataset target/background dimensions")
    if not np.isfinite(targets).all() or not np.isfinite(backgrounds).all():
        raise ValueError("Non-finite dataset target/background")
    for split, ids in expected_ids.items():
        if not np.array_equal(split_ids[split], ids):
            raise ValueError(f"Unexpected {split} view IDs")
    folders = {"appearance": "training", "joint": "training", "fixed": "density_control", "adaptive": "density_control"}
    audit = read_json("results/validation/reconciliation/audit_report.json")
    rows, reloads, trajectories = [], [], []
    images = {}
    for run, topic in folders.items():
        folder = f"results/{topic}/{run}"
        training = read_json(f"{folder}/training_report.json")
        for stage in ("initial", "final"):
            with np.load(ROOT / folder / stage / "rgb_float.npz", allow_pickle=False) as data:
                prediction = data["rgb"].astype(np.float64)
            if prediction.shape != targets.shape or not np.isfinite(prediction).all():
                raise ValueError(f"{run}/{stage}: invalid RGB shape or values")
            images[(run, stage)] = prediction
            saved = read_json(f"{folder}/{stage}/metrics.json")
            for split, ids in split_ids.items():
                diff = prediction[ids] - targets[ids]
                sse = float(np.sum(diff**2, dtype=np.float64))
                mse = sse / diff.size
                psnr = None if mse == 0 else -10 * math.log10(mse)
                mask = np.max(np.abs(targets[ids] - backgrounds[ids, None, None, :]), axis=-1) > 0.03
                contrast = float(np.mean(diff[mask]**2, dtype=np.float64)) if mask.any() else None
                actual = {"sse": sse, "scalar_count": int(diff.size), "mse": mse, "psnr_db": psnr,
                          "psnr_is_infinite": mse == 0, "max_abs_error": float(np.max(np.abs(diff))),
                          "contrast_mask_pixel_count": int(mask.sum()), "contrast_mask_mse": contrast}
                expected_groups = {
                    "saved metrics": saved[split],
                    "training report": training[f"{stage}_metrics"][split],
                    "independent historical audit": audit["recomputed_metrics"][run][stage][split],
                }
                for label, expected in expected_groups.items():
                    for key, value in actual.items():
                        if not numeric_close(value, expected[key]):
                            errors.append(f"{run}/{stage}/{split}: {key} differs from {label}")
                    if expected["view_ids"] != ids.tolist():
                        errors.append(f"{run}/{stage}/{split}: view IDs differ from {label}")
                rows.append({"run": run, "stage": stage, "split": split, **actual})
        with np.load(ROOT / f"{folder}_reload/rgb_float.npz", allow_pickle=False) as data:
            reloaded = data["rgb"].astype(np.float64)
        if reloaded.shape != targets.shape or not np.isfinite(reloaded).all():
            raise ValueError(f"{run}: invalid reloaded RGB")
        difference = float(np.max(np.abs(reloaded - images[(run, "final")])))
        if difference != 0:
            errors.append(f"{run}: archived reload differs from final RGB")
        reloads.append({"run": run, "max_abs_rgb_difference": difference})

    for left, right in [(('appearance','initial'),('joint','initial')),
                        (('joint','final'),('fixed','initial')),
                        (('joint','final'),('adaptive','initial'))]:
        if not np.array_equal(images[left], images[right]):
            errors.append(f"Paired starting image mismatch: {left} vs {right}")

    for model in ("fixed", "adaptive"):
        folder = ROOT / f"results/validation/{model}_review"
        report = read_json(f"results/validation/{model}_review/render_report.json")
        with np.load(folder / "trajectory_float.npz", allow_pickle=False) as data:
            rgb, c2w, w2c = data["rgb"], data["c2w_cv"], data["viewmats"]
        if rgb.shape != (61, 64, 96, 3) or c2w.shape != (61, 4, 4) or w2c.shape != (61, 4, 4):
            raise ValueError(f"{model}: unexpected trajectory dimensions")
        if not all(np.isfinite(x).all() for x in (rgb,c2w,w2c)):
            raise ValueError(f"{model}: non-finite trajectory data")
        frame_names = [p.name for p in sorted((folder/'frames').glob('frame_*.png'))]
        if frame_names != [f"frame_{i:03d}.png" for i in range(61)]:
            errors.append(f"{model}: trajectory PNG sequence incomplete")
        repeat = float(np.max(np.abs(rgb[0].astype(np.float64) - rgb[-1].astype(np.float64))))
        anchor = float(np.max(np.abs(rgb[0].astype(np.float64) - images[(model, 'final')][0])))
        if repeat != 0 or not np.array_equal(c2w[0], c2w[-1]):
            errors.append(f"{model}: saved trajectory does not return to identical A")
        if not np.allclose(rgb[0], images[(model,'final')][0], atol=2e-6, rtol=2e-5):
            errors.append(f"{model}: saved trajectory start differs from final view 0")
        for name, expected_hash in report['artifact_hashes'].items():
            if hashlib.sha256((folder/name).read_bytes()).hexdigest() != expected_hash:
                errors.append(f"{model}: historical artifact hash mismatch: {name}")
        audit_bytes = (ROOT/'results/validation/reconciliation/audit_report.json').read_bytes()
        if report['audit_sha256'] != hashlib.sha256(audit_bytes).hexdigest():
            errors.append(f"{model}: frozen report refers to a different audit")
        trajectories.append({"model": model, "frames": len(rgb), "return_max_abs_rgb_difference": repeat,
                             "start_vs_final_view0_max_abs_difference": anchor})
    return {"numpy_version": np.__version__, "conditions": rows, "reloads": reloads,
            "trajectories": trajectories, "paired_initial_images_match": not any('starting image' in e for e in errors),
            "scope": "Archived float arrays only. No training, rendering, CUDA execution or checkpoint loading."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recompute-metrics", action="store_true", help="Recompute 16 split/stage metrics with NumPy")
    parser.add_argument("--output", type=Path, help="Optionally save this check as JSON")
    args = parser.parse_args()
    errors = []
    report = {"schema_version": 1, "package": ROOT.name}
    checks = [("archive", archive_check), ("documents", document_check), ("package_files", package_check)]
    if args.recompute_metrics:
        checks.append(("metrics", recompute_metrics))
    for name, check in checks:
        try:
            report[name] = check(errors)
        except ImportError:
            errors.append("NumPy is required for metric recomputation: python -m pip install numpy")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"{name}: {exc}")
    report["status"] = "PASS" if not errors else "FAIL"
    report["errors"] = errors
    payload = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
