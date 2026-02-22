#!/usr/bin/env python3
import argparse
import base64
import json
import mimetypes
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _parse_sips_dimensions(image_path: Path) -> tuple[int, int]:
    cmd = ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(image_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"sips failed: {result.stderr.strip() or result.stdout.strip()}")
    content = (result.stdout or "") + "\n" + (result.stderr or "")
    m_w = re.search(r"pixelWidth:\s*(\d+)", content)
    m_h = re.search(r"pixelHeight:\s*(\d+)", content)
    if not m_w or not m_h:
        raise RuntimeError(f"cannot parse image dimensions from sips output: {content[:200]}")
    return int(m_w.group(1)), int(m_h.group(1))


def _ratio_check(width: int, height: int, expected_ratio: float, tolerance: float) -> tuple[bool, float]:
    if height <= 0:
        return False, 0.0
    actual = width / height
    return abs(actual - expected_ratio) <= tolerance, actual


def _image_to_data_url(image_path: Path) -> str:
    mime = mimetypes.guess_type(str(image_path))[0] or "image/jpeg"
    data = image_path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _extract_json_text(resp_obj: dict) -> str:
    output_text = resp_obj.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    # Fallback for non-standard response shapes.
    stack = [resp_obj]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            for key in ("text", "content", "value"):
                v = node.get(key)
                if isinstance(v, str):
                    raw = v.strip()
                    if raw.startswith("{") and raw.endswith("}"):
                        return raw
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)

    raise RuntimeError("cannot find JSON output in OpenAI response")


def _openai_image_qa(
    *,
    image_path: Path,
    model: str,
    expected_ratio: str,
    text_policy: str,
    allowed_text: list[str],
    extra_requirements: list[str],
    base_url: str,
) -> dict:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("missing OPENAI_API_KEY for AI image QA")

    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "pass": {"type": "boolean"},
            "failures": {"type": "array", "items": {"type": "string"}},
            "suggested_prompt_fixes": {"type": "array", "items": {"type": "string"}},
            "observed_text": {"type": "array", "items": {"type": "string"}},
            "summary": {"type": "string"},
        },
        "required": ["pass", "failures", "suggested_prompt_fixes", "observed_text", "summary"],
    }

    requirement_lines = [
        f"- Aspect ratio must be {expected_ratio}.",
        "- Must not contain watermark/logo/QR/version-corner labels.",
        "- Must keep character identity consistency (face, hair silhouette).",
        "- Must keep style consistency with the same material baseline.",
    ]

    if text_policy == "no_text":
        requirement_lines.append("- No visible text is allowed at all (Chinese/English/numbers/symbols).")
    elif text_policy == "whitelist":
        if allowed_text:
            requirement_lines.append("- Visible text must be strictly in this whitelist only:")
            for t in allowed_text:
                requirement_lines.append(f"  - {t}")
        else:
            requirement_lines.append("- Whitelist mode is enabled; if no whitelist text is provided, any visible text should fail.")
    else:
        requirement_lines.append("- Text is optional unless it violates any explicit requirement.")

    for r in extra_requirements:
        requirement_lines.append(f"- {r}")

    instruction = "\n".join(
        [
            "You are a strict image QA reviewer.",
            "Evaluate whether the image passes ALL hard requirements.",
            "If any requirement fails, set pass=false.",
            "Return JSON only and follow the schema exactly.",
            "Requirements:",
            *requirement_lines,
        ]
    )

    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": instruction},
                    {"type": "input_image", "image_url": _image_to_data_url(image_path)},
                ],
            }
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "image_qa_result",
                "schema": schema,
                "strict": True,
            }
        },
    }

    req = urllib.request.Request(
        base_url.rstrip("/") + "/responses",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI QA request failed: HTTP {exc.code} {exc.reason}; body={detail[:500]}") from exc

    obj = json.loads(body)
    text = _extract_json_text(obj)
    qa = json.loads(text)
    return qa


def _run_coze_generate(
    *,
    prompt: str,
    out_dir: Path,
    profile: str,
    prefix: str,
    seq: int,
    pad: int,
    ref_image: str | None,
    session_id: str | None,
) -> None:
    script_path = Path(__file__).resolve().with_name("coze_generate.py")
    if not script_path.exists():
        raise RuntimeError(f"missing coze_generate.py: {script_path}")

    env = os.environ.copy()
    env["COZE_IMAGE_PREFIX"] = prefix
    env["COZE_IMAGE_SEQ_START"] = str(seq)
    env["COZE_IMAGE_PAD"] = str(pad)
    env["COZE_IMAGE_INCLUDE_RUN_ID"] = "0"
    if session_id:
        env["COZE_SESSION_ID"] = session_id

    cmd = [
        sys.executable,
        str(script_path),
        prompt,
        "--profile",
        profile,
        "--out-dir",
        str(out_dir),
        "--no-run-id",
    ]
    if ref_image:
        cmd.extend(["--ref-image", ref_image])

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(
            "coze_generate.py failed\n"
            f"stdout:\n{result.stdout[-2000:]}\n"
            f"stderr:\n{result.stderr[-2000:]}"
        )


def _find_generated_image(out_dir: Path, prefix: str, seq: int, pad: int) -> Path:
    pattern = f"{prefix}_{str(seq).zfill(pad)}.*"
    files = sorted(out_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    for f in files:
        if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            return f
    raise RuntimeError(f"no generated image found for pattern {pattern} in {out_dir}")


def _cleanup_target_slot(out_dir: Path, prefix: str, seq: int, pad: int) -> None:
    pattern = f"{prefix}_{str(seq).zfill(pad)}.*"
    for f in out_dir.glob(pattern):
        if f.is_file():
            try:
                f.unlink()
            except Exception:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate image via Coze and run AI QA. On fail: delete and retry same image index.",
    )
    parser.add_argument("prompt", help="Base generation prompt")
    parser.add_argument("--profile", choices=["wechat_cover", "wechat_insert", "xhs"], required=True)
    parser.add_argument("--out-dir", required=True, help="Output image folder")
    parser.add_argument("--prefix", required=True, help="Image filename prefix, e.g. xhs or wechat_cover")
    parser.add_argument("--seq", type=int, required=True, help="Image sequence index, e.g. 1")
    parser.add_argument("--pad", type=int, default=2, help="Sequence zero-padding width (default: 2)")
    parser.add_argument("--ref-image", default="auto", help="Reference portrait path or auto (default: auto)")
    parser.add_argument("--session-id", default=None, help="Stable COZE_SESSION_ID for one material")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retries per image (default: 3)")
    parser.add_argument("--qa-platform", choices=["wechat", "xhs"], required=True)
    parser.add_argument("--require-no-text", action="store_true", help="Hard no-text policy")
    parser.add_argument("--allowed-text", action="append", default=[], help="Whitelisted on-image text (repeatable)")
    parser.add_argument("--allowed-text-file", default=None, help="One text line per allowed on-image text")
    parser.add_argument("--extra-requirement", action="append", default=[], help="Extra QA requirement (repeatable)")
    parser.add_argument("--ratio-tolerance", type=float, default=0.03, help="Ratio tolerance (default: 0.03)")
    parser.add_argument("--model", default="gpt-4.1-mini", help="OpenAI model for image QA")
    parser.add_argument("--openai-base-url", default="https://api.openai.com/v1", help="OpenAI API base URL")
    parser.add_argument("--keep-failed", action="store_true", help="Do not delete failed images")
    parser.add_argument("--qa-report", default=None, help="Optional path to write final QA JSON report")
    args = parser.parse_args()

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.qa_platform == "xhs" and args.profile != "xhs":
        raise SystemExit("--qa-platform xhs requires --profile xhs")
    if args.qa_platform == "wechat" and args.profile == "xhs":
        raise SystemExit("--qa-platform wechat cannot use --profile xhs")

    allowed_text = [t.strip() for t in (args.allowed_text or []) if t.strip()]
    if args.allowed_text_file:
        extra = [line.strip() for line in _read_text_file(Path(args.allowed_text_file).expanduser().resolve()).splitlines()]
        allowed_text.extend([x for x in extra if x])

    expected_ratio_value = 9 / 16 if args.profile == "xhs" else 4 / 3
    expected_ratio_label = "9:16" if args.profile == "xhs" else "4:3"

    text_policy = "optional"
    if args.require_no_text or args.profile == "wechat_cover":
        text_policy = "no_text"
    elif allowed_text:
        text_policy = "whitelist"

    last_qa: dict | None = None
    corrections: list[str] = []

    for attempt in range(1, args.max_retries + 1):
        prompt = args.prompt
        if corrections:
            correction_lines = "\n".join(f"- {c}" for c in corrections)
            prompt = (
                f"{prompt}\n\n"
                f"[QA Retry Constraints - Attempt {attempt}]\n"
                f"Fix all issues below and regenerate the same image index:\n"
                f"{correction_lines}\n"
                "Do not introduce new style family. Keep the same style baseline and same character identity."
            )

        _cleanup_target_slot(out_dir, args.prefix, args.seq, args.pad)
        _run_coze_generate(
            prompt=prompt,
            out_dir=out_dir,
            profile=args.profile,
            prefix=args.prefix,
            seq=args.seq,
            pad=args.pad,
            ref_image=args.ref_image,
            session_id=args.session_id,
        )

        image_path = _find_generated_image(out_dir, args.prefix, args.seq, args.pad)
        width, height = _parse_sips_dimensions(image_path)
        ratio_ok, actual_ratio = _ratio_check(width, height, expected_ratio_value, args.ratio_tolerance)

        local_failures: list[str] = []
        if not ratio_ok:
            local_failures.append(
                f"aspect ratio mismatch: expected {expected_ratio_label}, got {width}x{height} ({actual_ratio:.4f})"
            )

        qa: dict
        if local_failures:
            qa = {
                "pass": False,
                "failures": local_failures,
                "suggested_prompt_fixes": [
                    f"force exact {expected_ratio_label} output, keep composition within that ratio"
                ],
                "observed_text": [],
                "summary": "failed by local ratio check",
            }
        else:
            qa = _openai_image_qa(
                image_path=image_path,
                model=args.model,
                expected_ratio=expected_ratio_label,
                text_policy=text_policy,
                allowed_text=allowed_text,
                extra_requirements=args.extra_requirement,
                base_url=args.openai_base_url,
            )

        last_qa = qa
        passed = bool(qa.get("pass"))
        failures = [str(x).strip() for x in (qa.get("failures") or []) if str(x).strip()]
        fixes = [str(x).strip() for x in (qa.get("suggested_prompt_fixes") or []) if str(x).strip()]

        if passed:
            result = {
                "pass": True,
                "attempt": attempt,
                "image_path": str(image_path),
                "qa": qa,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            if args.qa_report:
                Path(args.qa_report).expanduser().resolve().write_text(
                    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            return 0

        print(f"[attempt {attempt}] QA failed: {image_path}")
        for i, f in enumerate(failures, 1):
            print(f"  {i}. {f}")

        if not args.keep_failed:
            try:
                image_path.unlink(missing_ok=True)
                print(f"  deleted failed image: {image_path}")
            except Exception as exc:
                print(f"  warning: failed to delete image {image_path}: {exc}")

        corrections = fixes + failures

    final = {
        "pass": False,
        "attempt": args.max_retries,
        "image_path": "",
        "qa": last_qa or {},
        "error": f"failed after {args.max_retries} attempts",
    }
    print(json.dumps(final, ensure_ascii=False, indent=2))
    if args.qa_report:
        Path(args.qa_report).expanduser().resolve().write_text(
            json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
