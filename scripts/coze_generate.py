#!/usr/bin/env python3
import argparse
import mimetypes
import json
import os
import re
import sys
import urllib.request
import urllib.error
import http.client
from pathlib import Path
from typing import List
import subprocess
import uuid
import random
import hashlib
from datetime import datetime

DEFAULT_URL = "https://vttznq9qz8.coze.site/stream_run"
DEFAULT_RUN_URL = "https://vttznq9qz8.coze.site/run"
DEFAULT_PROJECT_ID = "7602654205790388275"
DEFAULT_SESSION_ID = "bfemZV0f0e5zEMxzXCzqo"
DEFAULT_FILES_UPLOAD_URL = "https://api.coze.cn/v1/files/upload"

URL_RE = re.compile(
    r"https?://[^\s\"'<>]+\.(?:png|jpg|jpeg|webp)(?:\?[^\s\"'<>]+)?",
    re.IGNORECASE,
)

def _workspace_root() -> Path:
    root = (os.getenv("CODEX_WORKSPACE_ROOT") or os.getenv("WORKSPACE_ROOT") or "").strip()
    if root:
        return Path(root).expanduser()
    return Path.cwd()


def _skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _resolve_path(raw_path: str | Path) -> Path:
    workspace_root = _workspace_root()
    skill_root = _skill_root()

    raw = str(raw_path)
    p = Path(raw).expanduser()
    if p.is_absolute() and p.exists():
        return p
    if p.exists():
        return p

    candidates: list[Path] = []
    if not p.is_absolute():
        candidates.append(workspace_root / p)
        candidates.append(skill_root / p)

        parts = p.parts
        if len(parts) >= 2 and parts[0] == "skills" and parts[1] == "wechat-xhs-content":
            rest = Path(*parts[2:]) if len(parts) > 2 else Path(".")
            candidates.append(skill_root / rest)

    for c in candidates:
        if c.exists():
            return c
    return p


def _load_dotenv() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    candidates = [
        base_dir / ".env.local",
        base_dir / ".env",
    ]
    env_path = next((p for p in candidates if p.exists()), None)
    if env_path is None:
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        return


def _read_token() -> str:
    _load_dotenv()
    token = os.getenv("COZE_API_TOKEN")
    if token:
        return token.strip()
    sys.stderr.write("Enter COZE_API_TOKEN (input hidden not supported):\n")
    sys.stderr.flush()
    return sys.stdin.readline().strip()


def _collect_urls(text: str) -> List[str]:
    # First, handle non-streaming JSON responses (e.g. COZE_USE_STREAM=0).
    # These commonly look like {"messages":[...]} where tool outputs embed image_urls.
    stripped = text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            obj = json.loads(text)
        except Exception:
            obj = None
        structured_urls = set()

        def _walk(node, parent_key: str = "") -> None:
            if isinstance(node, dict):
                # Common image object shapes:
                # - {"generated_image": {"url": "...", "file_type": "..."}}
                # - {"url": "...", "file_type": "..."} (when nested under an image-ish key)
                url = node.get("url")
                if isinstance(url, str) and url.startswith("http"):
                    parent = (parent_key or "").lower()
                    if "image" in parent or "picture" in parent or "photo" in parent or "file_type" in node:
                        structured_urls.add(url)

                for u in (node.get("image_urls") or []):
                    if isinstance(u, str) and u.startswith("http"):
                        structured_urls.add(u)

                for k, v in node.items():
                    _walk(v, str(k))
            elif isinstance(node, list):
                for item in node:
                    _walk(item, parent_key)

        _walk(obj)

        if isinstance(obj, dict):
            msgs = obj.get("messages")
            if isinstance(msgs, list):
                for m in msgs:
                    if not isinstance(m, dict):
                        continue
                    content = m.get("content")
                    if isinstance(content, str):
                        try:
                            parsed = json.loads(content)
                        except Exception:
                            parsed = None
                        _walk(parsed, "content")
                    else:
                        _walk(content, "content")

        if structured_urls:
            return sorted(structured_urls)

    structured_urls = set()
    # Parse SSE-style lines to extract signed URLs from tool responses.
    for line in text.splitlines():
        if not line.startswith("data: "):
            continue
        payload = line[6:].strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            obj = json.loads(payload)
        except Exception:
            continue
        content = obj.get("content") or {}
        tool_response = content.get("tool_response") or {}
        result = tool_response.get("result")
        if isinstance(result, dict):
            for u in result.get("image_urls", []) or []:
                if isinstance(u, str):
                    structured_urls.add(u)
            # Also support newer result shapes (e.g. {"generated_image": {"url": ...}}).
            try:
                structured_urls.update(_collect_urls(json.dumps(result)))
            except Exception:
                pass
            continue
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
            except Exception:
                parsed = None
            if isinstance(parsed, dict):
                for u in parsed.get("image_urls", []) or []:
                    if isinstance(u, str):
                        structured_urls.add(u)
                try:
                    structured_urls.update(_collect_urls(json.dumps(parsed)))
                except Exception:
                    pass
    if structured_urls:
        return sorted(structured_urls)
    urls = set(URL_RE.findall(text))
    # Strip common trailing punctuation from markdown/rendered links.
    cleaned = {u.rstrip("\\)]}>,.;\"'") for u in urls}
    return sorted(cleaned)

def _build_fallback_urls(original: str) -> List[str]:
    # Try without query string
    base = original.split("?", 1)[0]
    candidates = [original, base]
    # Try proxy endpoints on the custom domain
    proxy_base = "https://vttznq9qz8.coze.site"
    candidates.extend(
        [
            f"{proxy_base}/file?url={original}",
            f"{proxy_base}/download?url={original}",
            f"{proxy_base}/image?url={original}",
            f"{proxy_base}/proxy?url={original}",
        ]
    )
    return candidates


def _extract_uploaded_url(upload_response: dict) -> str | None:
    # Coze file upload response shapes may vary; try a few common paths.
    if not isinstance(upload_response, dict):
        return None
    for key in ("url", "file_url", "download_url"):
        v = upload_response.get(key)
        if isinstance(v, str) and v.startswith("http"):
            return v
    data = upload_response.get("data")
    if isinstance(data, dict):
        for key in ("url", "file_url", "download_url"):
            v = data.get(key)
            if isinstance(v, str) and v.startswith("http"):
                return v
    return None


def _encode_image_data_url(image_path: Path, max_dim: int = 256) -> str:
    image_path = _resolve_path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(str(image_path))
    tmp_dir = Path("/tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_dir / f"coze_ref_{uuid.uuid4().hex}{image_path.suffix or '.jpg'}"
    try:
        # Prefer downscaling to keep payload sizes reasonable.
        subprocess.run(
            ["sips", "-Z", str(max_dim), str(image_path), "--out", str(tmp_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        data = tmp_path.read_bytes()
    except Exception:
        data = image_path.read_bytes()
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass
    import base64

    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _build_payload(
    prompt_text: str,
    extra_parameters: dict | None = None,
    legacy_ref_image_data_url: str | None = None,
) -> dict:
    # Simple "Gemini Flow" style run endpoint: POST /run with {"text": "...", "reference_image": {...}}.
    # Enable via COZE_SIMPLE_WORKFLOW=1.
    if os.getenv("COZE_SIMPLE_WORKFLOW", "0").strip() == "1":
        payload: dict = {"text": prompt_text}
        if legacy_ref_image_data_url:
            payload["reference_image"] = {"url": legacy_ref_image_data_url, "file_type": "image"}
        else:
            payload["reference_image"] = ""
        return payload

    # Prefer official workflow API when workflow_id is available.
    workflow_id = os.getenv("COZE_WORKFLOW_ID")
    if workflow_id:
        parameters: dict = {
            "BOT_USER_INPUT": prompt_text,
        }
        if extra_parameters:
            parameters.update(extra_parameters)

        parameters_value: object
        # coze.cn workflow endpoints commonly expect `parameters` as a JSON string.
        if os.getenv("COZE_WORKFLOW_PARAMETERS_AS_OBJECT", "0").strip() == "1":
            parameters_value = parameters
        else:
            parameters_value = json.dumps(parameters, ensure_ascii=False)
        return {
            "workflow_id": workflow_id,
            "parameters": parameters_value,
        }

    # Fallback: legacy stream_run payload used by custom domain endpoints.
    project_id = os.getenv("COZE_PROJECT_ID", DEFAULT_PROJECT_ID)
    session_id = os.getenv("COZE_SESSION_ID", DEFAULT_SESSION_ID)
    prompt_items = [{"type": "text", "content": {"text": prompt_text}}]
    if legacy_ref_image_data_url:
        prompt_items.append(
            {"type": "image", "content": {"image_url": legacy_ref_image_data_url}}
        )
    return {
        "content": {
            "query": {
                "prompt": prompt_items
            }
        },
        "type": "query",
        "session_id": session_id,
        "project_id": int(project_id) if str(project_id).isdigit() else project_id,
    }

def _upload_file(file_path: Path, token: str) -> dict:
    if not file_path.exists():
        raise FileNotFoundError(str(file_path))
    upload_url = os.getenv("COZE_FILES_UPLOAD_URL", DEFAULT_FILES_UPLOAD_URL).strip() or DEFAULT_FILES_UPLOAD_URL

    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        mime_type = "application/octet-stream"

    boundary = "----cozeupload-" + uuid.uuid4().hex
    filename = file_path.name
    file_bytes = file_path.read_bytes()
    preamble = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode("utf-8")
    epilogue = f"\r\n--{boundary}--\r\n".encode("utf-8")
    body = preamble + file_bytes + epilogue

    req = urllib.request.Request(
        upload_url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
    try:
        obj = json.loads(raw)
    except Exception:
        raise RuntimeError(f"Upload failed; non-JSON response: {raw[:200]!r}")
    code = obj.get("code")
    if code not in (0, "0", None):
        raise RuntimeError(f"Upload failed; code={code!r} message={obj.get('msg') or obj.get('message')!r}")
    data = obj.get("data") or obj.get("result") or {}
    if not isinstance(data, dict) or not data:
        data = obj
    return data


def _post_json(url: str, payload: dict, token: str) -> str:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _post_stream(url: str, payload: dict, token: str) -> str:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        chunks = []
        found_early = False
        while True:
            try:
                chunk = resp.read(4096)
            except http.client.IncompleteRead as ir:
                chunk = ir.partial
            if not chunk:
                break
            text = chunk.decode("utf-8", errors="ignore")
            chunks.append(text)
            if URL_RE.search(text):
                found_early = True
                break
        raw = "".join(chunks)
        if found_early:
            try:
                extra = resp.read(4096).decode("utf-8", errors="ignore")
                raw += extra
            except Exception:
                pass
        return raw


def main() -> int:
    # Load .env/.env.local early so defaults (e.g. COZE_RUN_URL, COZE_REF_IMAGE_DEFAULT,
    # COZE_PROMPT_PREFIX_FILE) apply even when the user doesn't pass CLI flags.
    _load_dotenv()

    parser = argparse.ArgumentParser(
        description="Call Coze endpoints, extract image URLs, and optionally download images.",
    )
    parser.add_argument("prompt", help="Prompt text to send to Coze")
    parser.add_argument(
        "raw_output",
        nargs="?",
        help="Optional path to save the raw response (text/SSE payload)",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Directory to save downloaded images (overrides COZE_OUT_DIR). "
        "Relative paths are resolved from project root.",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help="Filename prefix for downloaded images (overrides COZE_IMAGE_PREFIX).",
    )
    parser.add_argument(
        "--workflow-id",
        default=None,
        help="Override COZE_WORKFLOW_ID for this run.",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Override COZE_SESSION_ID for this run (legacy stream_run payload).",
    )
    parser.add_argument(
        "--new-session",
        action="store_true",
        help="Generate a fresh random session id for this run (avoids history contamination).",
    )
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="Extra workflow parameter KEY=VALUE (repeatable). Only used with COZE_WORKFLOW_ID.",
    )
    parser.add_argument(
        "--profile",
        choices=["wechat_cover", "wechat_insert", "xhs"],
        default=None,
        help=(
            "Apply a predefined prompt-prefix set to reduce mistakes. "
            "wechat_cover: global style + 4:3 no-text lock; "
            "wechat_insert: global style only; "
            "xhs: global style + 9:16 XHS poster lock."
        ),
    )
    parser.add_argument(
        "--prompt-prefix-file",
        action="append",
        default=[],
        help=(
            "Path to a text file to prepend to the prompt (repeatable). "
            "If omitted, uses COZE_PROMPT_PREFIX_FILE (comma-separated) when set."
        ),
    )
    parser.add_argument(
        "--ref-image",
        default=None,
        help=(
            "Path to a reference portrait image. Uploads to Coze and passes file_id into workflow parameters. "
            "Use 'auto' to randomly pick one from inputs/images/portraits/. "
            "If COZE_WORKFLOW_ID is not set, the image is embedded into the legacy stream_run prompt."
        ),
    )
    parser.add_argument(
        "--ref-param",
        default="PORTRAIT",
        help="Workflow input key to receive the reference image (default: PORTRAIT).",
    )
    parser.add_argument(
        "--ref-max-dim",
        type=int,
        default=256,
        help="Max dimension used when embedding reference image (default: 256).",
    )
    run_id_group = parser.add_mutually_exclusive_group()
    run_id_group.add_argument(
        "--include-run-id",
        dest="include_run_id",
        action="store_true",
        default=None,
        help="Include a run id in filenames (overrides COZE_IMAGE_INCLUDE_RUN_ID).",
    )
    run_id_group.add_argument(
        "--no-run-id",
        dest="include_run_id",
        action="store_false",
        default=None,
        help="Do not include a run id in filenames (overrides COZE_IMAGE_INCLUDE_RUN_ID).",
    )
    args = parser.parse_args()

    # Allow setting a default reference image via env var so new conversations can
    # run without repeating CLI flags.
    if not args.ref_image:
        env_ref = (os.getenv("COZE_REF_IMAGE_DEFAULT") or os.getenv("COZE_REF_IMAGE") or "").strip()
        if env_ref:
            args.ref_image = env_ref

    prompt_text = args.prompt
    def _profile_prefix_files(profile: str | None) -> list[str]:
        if not profile:
            return []
        skill_root = _skill_root()
        if profile == "wechat_cover":
            return [
                str(skill_root / "references/global_style_lock.txt"),
                str(skill_root / "references/wechat_cover_lock.txt"),
            ]
        if profile == "xhs":
            return [
                str(skill_root / "references/global_style_lock.txt"),
                str(skill_root / "references/xhs_poster_lock_9x16.txt"),
            ]
        if profile == "wechat_insert":
            return [str(skill_root / "references/global_style_lock.txt")]
        return []

    prefix_files: list[str] = []
    prefix_files.extend(_profile_prefix_files(args.profile))
    prefix_files.extend(list(args.prompt_prefix_file or []))

    env_value = os.getenv("COZE_PROMPT_PREFIX_FILE", "").strip()
    if env_value:
        prefix_files.extend([p.strip() for p in env_value.split(",") if p.strip()])

    # De-duplicate while preserving order.
    deduped: list[str] = []
    seen: set[str] = set()
    for p in prefix_files:
        if p in seen:
            continue
        seen.add(p)
        deduped.append(p)
    prefix_files = deduped

    if prefix_files:
        prefix_chunks: list[str] = []
        for raw_path in prefix_files:
            prefix_path = _resolve_path(raw_path)
            try:
                prefix_text = prefix_path.read_text(encoding="utf-8").strip()
            except Exception as exc:
                sys.stderr.write(
                    f"Failed to read --prompt-prefix-file {raw_path} (resolved to {prefix_path}): {exc}\n"
                    "Tip: use one of these locations:\n"
                    f"- {_skill_root() / 'references/global_style_lock.txt'}\n"
                    f"- {_skill_root() / 'references/wechat_cover_lock.txt'}\n"
                    f"- {_skill_root() / 'references/xhs_poster_lock_9x16.txt'}\n"
                    f"- {_workspace_root() / 'inputs/images/portraits'} (for portraits; not a prefix file)\n"
                )
                return 2
            if prefix_text:
                prefix_chunks.append(prefix_text)
        if prefix_chunks:
            prompt_text = "\n\n".join(prefix_chunks + [prompt_text])
    out_path = args.raw_output

    token = _read_token()
    if not token:
        sys.stderr.write("Missing COZE_API_TOKEN.\n")
        return 2

    if args.workflow_id:
        os.environ["COZE_WORKFLOW_ID"] = args.workflow_id.strip()
    if args.session_id:
        os.environ["COZE_SESSION_ID"] = args.session_id.strip()
    if args.new_session:
        os.environ["COZE_SESSION_ID"] = uuid.uuid4().hex

    workflow_id = os.getenv("COZE_WORKFLOW_ID", "").strip()

    extra_parameters: dict = {}
    legacy_ref_data_url: str | None = None
    if args.param:
        for item in args.param:
            if "=" not in item:
                sys.stderr.write(f"Invalid --param (expected KEY=VALUE): {item}\n")
                return 2
            k, v = item.split("=", 1)
            k = k.strip()
            if not k:
                sys.stderr.write(f"Invalid --param key: {item}\n")
                return 2
            extra_parameters[k] = v

    if args.ref_image:
        ref_value = str(args.ref_image).strip()
        if ref_value.lower() == "auto":
            workspace_root = _workspace_root()
            skill_root = _skill_root()
            # By default, only sample from the workspace portraits (the user's photos).
            # Opt-in to include skill-provided portraits via env.
            auto_dirs_env = os.getenv("COZE_REF_IMAGE_AUTO_DIRS", "").strip()
            if auto_dirs_env:
                portraits_dirs = [Path(p.strip()) for p in auto_dirs_env.split(",") if p.strip()]
            else:
                portraits_dirs = [workspace_root / "inputs" / "images" / "portraits"]
                if os.getenv("COZE_REF_IMAGE_AUTO_INCLUDE_SKILL", "0").strip() == "1":
                    portraits_dirs.append(skill_root / "assets" / "portraits")
            candidates = []
            for portraits_dir in portraits_dirs:
                if not portraits_dir.exists():
                    continue
                candidates.extend(sorted(portraits_dir.glob("*.jpg")))
                candidates.extend(sorted(portraits_dir.glob("*.jpeg")))
                candidates.extend(sorted(portraits_dir.glob("*.png")))
            if not candidates:
                sys.stderr.write(
                    "No portraits found. Put portrait images under either:\n"
                    f"- {_workspace_root() / 'inputs/images/portraits'}\n"
                    f"- {_skill_root() / 'assets/portraits'}\n"
                )
                return 2
            # Allow pinning a specific portrait via env var.
            pinned = (os.getenv("COZE_REF_IMAGE") or "").strip()
            if pinned:
                ref_path = _resolve_path(pinned)
                if not ref_path.exists():
                    sys.stderr.write(f"COZE_REF_IMAGE set but file not found: {ref_path}\n")
                    return 2
            else:
                # Deterministic selection improves consistency across multiple images
                # when the caller reuses the same session id.
                seed = (os.getenv("COZE_SESSION_ID") or os.getenv("COZE_REF_SEED") or "").strip()
                if seed:
                    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
                    idx = int(digest, 16) % len(candidates)
                    ref_path = candidates[idx]
                else:
                    ref_path = random.choice(candidates)
            print(f"=== Using ref image ===\n{ref_path}")
        else:
            ref_path = _resolve_path(ref_value)
        if workflow_id:
            uploaded = _upload_file(ref_path, token)
            file_id = uploaded.get("id") or uploaded.get("file_id")
            if not file_id:
                sys.stderr.write("Upload succeeded but no file id found in response.\n")
                return 2
            extra_parameters[args.ref_param] = {"file_id": file_id}
        else:
            # Non-workflow modes:
            # - COZE_SIMPLE_WORKFLOW=1: prefer uploading and passing a remote URL to the /run endpoint.
            # - otherwise: legacy proxy embeds as a data URL prompt item.
            if os.getenv("COZE_SIMPLE_WORKFLOW", "0").strip() == "1":
                try:
                    uploaded_url = None
                    try:
                        uploaded = _upload_file(ref_path, token)
                        uploaded_url = _extract_uploaded_url(uploaded)
                    except Exception:
                        uploaded_url = None
                    if uploaded_url:
                        legacy_ref_data_url = uploaded_url
                    else:
                        legacy_ref_data_url = _encode_image_data_url(
                            ref_path, max_dim=max(64, int(args.ref_max_dim))
                        )
                except Exception as exc:
                    sys.stderr.write(f"Failed to prepare ref image: {exc}\n")
                    return 2
            else:
                try:
                    legacy_ref_data_url = _encode_image_data_url(
                        ref_path, max_dim=max(64, int(args.ref_max_dim))
                    )
                except Exception as exc:
                    sys.stderr.write(f"Failed to embed ref image: {exc}\n")
                    return 2

    url = os.getenv("COZE_STREAM_URL", DEFAULT_URL)
    run_url = os.getenv("COZE_RUN_URL", DEFAULT_RUN_URL)
    payload = _build_payload(
        prompt_text,
        extra_parameters if extra_parameters else None,
        legacy_ref_image_data_url=legacy_ref_data_url,
    )

    try:
        use_stream = os.getenv("COZE_USE_STREAM", "1").strip() != "0"
        if use_stream:
            raw = _post_stream(url, payload, token)
        else:
            raw = _post_json(run_url, payload, token)
    except Exception as exc:
        # Fallback to non-streaming run endpoint if stream failed.
        try:
            raw = _post_json(run_url, payload, token)
        except Exception as exc2:
            sys.stderr.write(f"Request failed: {exc}\nFallback failed: {exc2}\n")
            return 1

    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(raw)

    urls = _collect_urls(raw)
    print("=== Raw Response (truncated) ===")
    print(raw[:2000])
    print("=== Detected Image URLs ===")
    if urls:
        for u in urls:
            print(u)
    else:
        print("(none detected; provide a sample response to refine parsing)")

    if urls:
        workspace_root = _workspace_root()
        out_dir_env = os.getenv("COZE_OUT_DIR", "").strip()
        out_dir_arg = (args.out_dir or "").strip()
        out_dir_value = out_dir_arg or out_dir_env
        if out_dir_value:
            out_dir = Path(out_dir_value)
            if not out_dir.is_absolute():
                out_dir = workspace_root / out_dir
        else:
            out_dir = workspace_root / "outputs" / "images"
        out_dir.mkdir(parents=True, exist_ok=True)
        prefix = (args.prefix or "").strip() or os.getenv("COZE_IMAGE_PREFIX", "coze").strip() or "coze"
        safe_prefix = re.sub(r"[^a-zA-Z0-9_-]+", "_", prefix)
        include_run_id_env = os.getenv("COZE_IMAGE_INCLUDE_RUN_ID", "1").strip() != "0"
        include_run_id = include_run_id_env if args.include_run_id is None else bool(args.include_run_id)
        run_id = os.getenv("COZE_IMAGE_RUN_ID", "").strip()
        if not run_id:
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
        try:
            seq_start = int(os.getenv("COZE_IMAGE_SEQ_START", "1"))
        except ValueError:
            seq_start = 1
        try:
            seq_pad = int(os.getenv("COZE_IMAGE_PAD", "2"))
        except ValueError:
            seq_pad = 2
        try:
            min_bytes = int(os.getenv("COZE_MIN_IMAGE_BYTES", "50000"))
        except ValueError:
            min_bytes = 50000
        save_raw = os.getenv("COZE_SAVE_RAW", "0").strip() == "1"
        invalid_dir_env = os.getenv("COZE_INVALID_DIR", "").strip()
        invalid_dir = (
            Path(invalid_dir_env)
            if invalid_dir_env
            else (workspace_root / "outputs" / "archive" / "invalid_outputs")
        )
        if not invalid_dir.is_absolute():
            invalid_dir = workspace_root / invalid_dir
        if save_raw:
            invalid_dir.mkdir(parents=True, exist_ok=True)
        print("=== Downloaded Files ===")
        for offset, u in enumerate(urls, 0):
            idx = seq_start + offset
            seq = str(idx).zfill(seq_pad)
            base_url = u.split("?", 1)[0]
            suffix = Path(base_url).suffix.lower()
            if suffix not in (".png", ".jpg", ".jpeg", ".webp"):
                suffix = ".jpg"
            if include_run_id:
                filename = out_dir / f"{safe_prefix}_{run_id}_{seq}{suffix}"
            else:
                filename = out_dir / f"{safe_prefix}_{seq}{suffix}"
            try:
                # Try multiple header variants in case the storage URL is strict.
                header_sets = [
                    {},  # plain
                    {"User-Agent": "Mozilla/5.0"},
                    {
                        "User-Agent": "Mozilla/5.0",
                        "Referer": "https://vttznq9qz8.coze.site/",
                        "Origin": "https://vttznq9qz8.coze.site",
                    },
                    {
                        "User-Agent": "Mozilla/5.0",
                        "Authorization": f"Bearer {token}",
                    },
                ]
                data = None
                last_err = None
                for headers in header_sets:
                    try:
                        req_img = urllib.request.Request(u, headers=headers)
                        with urllib.request.urlopen(req_img, timeout=120) as resp:
                            data = resp.read()
                        last_err = None
                        break
                    except urllib.error.HTTPError as http_exc:
                        body = http_exc.read()
                        last_err = Exception(
                            f"HTTP {http_exc.code} {http_exc.reason}; "
                            f"headers={dict(http_exc.headers)}; body={body[:200]!r}"
                        )
                        continue
                    except Exception as exc:
                        last_err = exc
                        continue
                if data is None:
                    raise last_err or Exception("download failed")
                if len(data) < min_bytes:
                    print(f"(warning) small file {len(data)} bytes: {filename}")
                    if save_raw:
                        err_path = invalid_dir / (filename.stem + ".txt")
                        try:
                            err_path.write_bytes(data)
                            print(f"(saved) {err_path}")
                        except Exception:
                            pass
                    continue
                with open(filename, "wb") as f:
                    f.write(data)
                print(str(filename))
            except Exception as exc:
                # Fallback: try alternative URLs (no query / proxy).
                downloaded = False
                for alt in _build_fallback_urls(u):
                    try:
                        req_alt = urllib.request.Request(
                            alt,
                            headers={
                                "User-Agent": "Mozilla/5.0",
                                "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                            },
                        )
                        with urllib.request.urlopen(req_alt, timeout=120) as resp:
                            alt_data = resp.read()
                        if len(alt_data) >= min_bytes:
                            with open(filename, "wb") as f:
                                f.write(alt_data)
                            print(str(filename))
                            downloaded = True
                            break
                    except Exception:
                        continue
                if downloaded:
                    continue
                # Fallback to curl, some storage URLs block urllib.
                try:
                    result = subprocess.run(
                        [
                            "curl",
                            "-L",
                            "-o",
                            str(filename),
                            "-H",
                            "User-Agent: Mozilla/5.0",
                            "-H",
                            "Accept: image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                            u,
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    size = filename.stat().st_size if filename.exists() else 0
                    if size < min_bytes:
                        print(f"(warning) small file {size} bytes: {filename}")
                        try:
                            filename.unlink(missing_ok=True)
                        except Exception:
                            pass
                    else:
                        print(str(filename))
                except Exception as exc2:
                    print(f"(failed) {u} -> {exc} | curl: {exc2}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
