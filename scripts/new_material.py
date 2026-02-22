#!/usr/bin/env python3
import argparse
import os
import re
from datetime import datetime
from pathlib import Path


INVALID_CHARS_RE = re.compile(r"[\/\\:\*\?\"<>\|\n\r\t]+")
WHITESPACE_RE = re.compile(r"\s+")


def _sanitize_material_name(name: str, max_len: int = 30) -> str:
    name = (name or "").strip()
    name = INVALID_CHARS_RE.sub(" ", name)
    name = WHITESPACE_RE.sub(" ", name).strip()
    if len(name) > max_len:
        name = name[:max_len].rstrip()
    return name


def _workspace_root() -> Path:
    root = (os.getenv("CODEX_WORKSPACE_ROOT") or os.getenv("WORKSPACE_ROOT") or "").strip()
    if root:
        return Path(root).expanduser()
    return Path.cwd()


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an output folder for a new content material.")
    parser.add_argument("name", help="Material name (short, human-readable; Chinese ok)")
    parser.add_argument(
        "--wechat-root",
        default="outputs/wechat",
        help="WeChat root output directory, relative to workspace root (default: outputs/wechat)",
    )
    parser.add_argument(
        "--xhs-root",
        default="outputs/xhs",
        help="XHS root output directory, relative to workspace root (default: outputs/xhs)",
    )
    parser.add_argument(
        "--timestamp",
        default=None,
        help="Override timestamp (format: YYYYMMDD_HHMMSS). Default: now (local time).",
    )
    parser.add_argument(
        "--no-template",
        action="store_true",
        help="Do not create the 00_brief.md template file.",
    )
    args = parser.parse_args()

    workspace_root = _workspace_root()
    skill_root = Path(__file__).resolve().parent.parent
    wechat_root = Path(args.wechat_root)
    if not wechat_root.is_absolute():
        wechat_root = workspace_root / wechat_root
    wechat_root.mkdir(parents=True, exist_ok=True)

    xhs_root = Path(args.xhs_root)
    if not xhs_root.is_absolute():
        xhs_root = workspace_root / xhs_root
    xhs_root.mkdir(parents=True, exist_ok=True)

    ts = (args.timestamp or "").strip() or datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = _sanitize_material_name(args.name)
    folder_name = f"{ts}_{safe_name}" if safe_name else ts

    wechat_dir = wechat_root / folder_name
    wechat_dir.mkdir(parents=True, exist_ok=False)
    (wechat_dir / "images").mkdir(parents=True, exist_ok=True)

    xhs_dir = xhs_root / folder_name
    xhs_dir.mkdir(parents=True, exist_ok=False)
    (xhs_dir / "images").mkdir(parents=True, exist_ok=True)

    if not args.no_template:
        brief_path = wechat_dir / "00_brief.md"
        brief_path.write_text(
            "\n".join(
                [
                    "# 写作简报（待确认）",
                    "",
                    "## 选题一句话（原话）",
                    "",
                    "## 目标读者 & 期望动作",
                    "",
                    "## 真实起因（1个场景）& 最难受的点",
                    "",
                    "## 我做了什么（3–6步）",
                    "",
                    "## 踩坑与关键调整（2–4条）",
                    "",
                    "## 结果证据（数字优先；不够标“待补”）",
                    "",
                    "## 结构选择（叙事/清单/短论）& 理由",
                    "",
                    "## 禁区（不要写/不要夸大/不要虚构）",
                    "",
                    "## 最关键的3个反问（补齐缺口）",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        visual_brief_path = wechat_dir / "visual_brief.md"
        style_lock_path = skill_root / "references" / "global_style_lock.txt"
        visual_brief_path.write_text(
            "\n".join(
                [
                    "【本次内容的视觉母题｜只回答“这篇文章的图要表达什么”】【不等于某一张图画什么】",
                    "",
                    "填充时机：公众号文章写完并确认后，再来写本文件。",
                    "",
                    "建议结构：",
                    "- 这篇文章必须被图像强化的核心观点（2–4条）",
                    "- 必须反复出现的视觉意象（系列识别点）",
                    "- 允许出现的场景库（围绕整篇内容）",
                    "- 绝对不做的表达",
                    "- 生图拼装规则：全局风格锁 + 本文件 + 单图场景补充 + 真人 portraits",
                    "",
                    f"全局风格锁：{style_lock_path}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )


    print(str(wechat_dir))
    print(str(xhs_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
