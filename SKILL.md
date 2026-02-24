---
name: wechat-xhs-content
description: Create and refine WeChat public account articles and Xiaohongshu image-first posts for AI-savvy product/knowledge workers, including topic selection, outline, copywriting, image storyboard, and platform-specific packaging. Use when drafting ~2500 Chinese-character WeChat pieces (target 2400–2600), converting a topic into a Xiaohongshu multi-image narrative, or generating image prompts that keep a consistent Q-style main character.
---

# WeChat + 小红书内容工作流

## Quick Start

Follow this workflow every time unless the user requests a subset.

**IMPORTANT: Before any writing, you MUST read and deeply understand `references/my_voice.md` and `references/user_voice_sample.md`. Your primary goal is to mimic the voice and thought process in these files, not just to follow the structural rules. The voice defined in `my_voice.md` OVERRIDES all other stylistic instructions.**

0. Create per-material folders under `outputs/wechat/` and `outputs/xhs/` (same `<material_id>`; see “Material Folder Rules”).
1. Ask deep-dive questions (can be multi-round) to unpack the user’s story before writing.
2. Wait for the user’s answers; only proceed after the user says “可以/开始/就按这个写”.
3. If (and only if) the user explicitly provides a source document path, read it.
4. Write a **writing brief** (`00_brief.md`) into the material folder and **stop** for user confirmation.
5. Draft the WeChat article (2400–2600 Chinese characters, target ~2500; include section subtitles) and save to the material folder.
6. **Stop and wait for user approval** (“OK/继续/通过”) before proceeding.
7. Generate a WeChat image plan + image prompts and save as a separate notes file in the material folder.
8. **Stop and wait for user approval** (“OK/继续/通过”) before generating any images.
9. Generate **only the first** WeChat image prompt and, if asked to generate images, produce **only the first image**; run the mandatory image QA loop until pass.
10. Wait for user confirmation that the style is OK (“风格OK/继续”), then generate the remaining WeChat images/prompts with per-image QA; after all pass, return to `wechat_article.md` and mark where each image should be inserted.
11. Build the Xiaohongshu outline/storyboard (text only) and wait for user approval.
12. Generate **only the first** Xiaohongshu image prompt and, if asked to generate images, produce **only the first image**; run the mandatory image QA loop until pass.
13. Wait for user confirmation that the style is OK (“风格OK/继续”), then generate the remaining Xiaohongshu images/prompts with per-image QA and complete `xhs_post.md` (caption + hashtags).

If examples are needed, read `references/samples.md`.
If voice, structure, or visual rules are needed, read the related references listed below.
Default: apply the “去 AI 味” constraints listed in this SKILL (no extra steps).

**Dynamic Blacklist:** Create and maintain a file named `references/ai_taste_blacklist.md`. If the user points out any word or phrase as having "AI taste", immediately append it to this file. Before generating any text, always read this file and strictly avoid using any blacklisted terms.

## Inputs to Ask For (keep brief)

Ask only when missing:

- Topic / material name (1 sentence; used for folder naming)
- Audience and desired outcome
- Any constraints (length, tone, deadlines)
- Clarifying Q&A required before writing (see “Clarifying Questions”)

Assume defaults if not provided:

- Audience: AI‑savvy product/knowledge workers
- WeChat length: 2400–2600 字（目标≈2500）
- Tone: Defined in `references/my_voice.md`. Must be conversational, personal, and avoid overly formal or "AI-like" language.
- XHS format: multi‑image + caption + tags (image count determined by content)
- XHS caption length: 500 字及以上（建议 500–700 字）
- Image tool: **Coze** (do not ask to choose tools)

## Deliverables

Always output in **separate files** with **clean content only**:

- Material brief (Q&A digest + decisions): `outputs/wechat/<material_id>/00_brief.md`
- WeChat draft (final article only + image placement markers after image phase): `outputs/wechat/<material_id>/wechat_article.md`
- WeChat notes (image plan + prompts): `outputs/wechat/<material_id>/wechat_notes.md`
- Xiaohongshu draft (storyboard + caption + prompts): `outputs/xhs/<material_id>/xhs_post.md`

Only after writing files, provide a short response that lists the updated file paths.

## Stage Gates (Hard Rule)

- Gate A: After clarifying Q&A, wait for “开始/就按这个写”.
- Gate B: After `00_brief.md`, wait for “OK/继续/通过”.
- Gate C: After WeChat article, wait for “OK/继续/通过”.
- Gate D: After `wechat_notes.md`, wait for “OK/继续/通过”.
- Gate E: After first WeChat image (QA pass), wait for “风格OK/继续”.
- Gate F: After XHS storyboard, wait for “OK/继续/通过”.
- Gate G: After first XHS image (QA pass), wait for “风格OK/继续”.

Do **not** proceed past a gate without explicit user confirmation.

## Brief File Rules (`00_brief.md`)

Purpose: lock the story and constraints before drafting, reduce “写偏了/写乱了”.

Keep it short and scannable (recommended ≤ 400–800 Chinese characters):

- 选题一句话（用用户原话）
- 目标读者 + 期望读完后的动作
- 真实起因（1 个场景）+ 最难受的点（1 句）
- 你做了什么（3–6 步流程，尽量具体到“文件/脚本/习惯”）
- 踩坑与关键调整（2–4 条）
- 结果证据（尽量数字化；不够就标“待补”并反问）
- 文章结构选择（默认叙事 / 清单干货 / 观点短论）+ 选择理由
- 禁区（哪些内容不要写/不要夸大/不要虚构）

End with: “我理解对不对？要不要改？” + 3 个最关键反问（用于最后补齐缺口）。

WeChat file content rules:

- **Only** the final article (title + 30字左右简介 + 正文).  
- 正文需要章节小标题，但数量由内容决定（不要写“第一部分/第二部分”这种模板标题）。
- **Do not** include outlines or image plans in the article file.
- After WeChat images pass QA, go back to `wechat_article.md` and add concise placement markers in-body (e.g., `[配图-01]`), so each image has a clear insertion position.
- Always write a **separate** WeChat notes file containing:
  - WeChat image plan (what images, style, where to place)
  - WeChat image prompts (per image)

Xiaohongshu file sections:

- Xiaohongshu storyboard (per image)
- Image prompts (per image)
- Xiaohongshu caption + hashtags

Never combine WeChat and XHS drafts into a single file.

## Output Hygiene (Hard Rule)

- Always write into `outputs/wechat/<material_id>/` and `outputs/xhs/<material_id>/` only.  
- Never write Markdown drafts directly under `outputs/` root.  
- Ensure directories exist before writing.

## Source Document Policy

- Do **not** read any source document unless the user explicitly provides the file path.
- If no path is provided, proceed with questions only and do not assume a default document.

## Material Folder Rules (Hard Rule)

For every new topic/material, create a dedicated folder under **both** platform directories using the same `<material_id>`:

- WeChat root: `outputs/wechat/YYYYMMDD_HHMMSS_<素材名>/`
  - Files: `00_brief.md`, `wechat_article.md`, `wechat_notes.md`
  - Images: `outputs/wechat/<material_id>/images/`
- XHS root: `outputs/xhs/YYYYMMDD_HHMMSS_<素材名>/`
  - Files: `xhs_post.md`
  - Images: `outputs/xhs/<material_id>/images/`

Naming:

- `YYYYMMDD_HHMMSS` uses local time.
- `<素材名>` is a short human-readable name (Chinese ok). Strip `/\\:*?\"<>|` and keep it ≤ 30 chars.

Optional helper:

- Create folders via `scripts/new_material.py "<素材名>"`

## Clarifying Questions (Required)

Before writing, ask deep‑dive questions that unpack the user’s story and help them think.
Prefer **multi-round**: ask 6–8 first, then ask 3–6 targeted follow-ups based on answers.
Avoid surface “配置型”问题.
Use groups like below (pick ~10–14 total across rounds):

**0. 声音样本（获取你的“原声”）**
- 你能不能用说话的方式，跟我讲讲这次想写的事？就像跟朋友聊天一样，不用整理，想到哪说到哪就行。三五句话或者一段语音笔记都可以。

**A. 起点与触发（还原真实起因）**
- 当时最真实的痛点是什么？一句话 + 一个具体场景。  
- 这个痛点最难受的是“耗时”“不确定”“沟通成本”还是“责任压力”？  
- 你在什么具体时刻意识到：必须试 AI？
- 开头你希望落在哪个“镜头”？按这个格式回答：**时间+地点+你在做什么+卡在哪一步+当时一句心里话**  
  - 例：周一 23:40，工位写 PRD，第 3 次把同一段背景复制到新对话，我心里想“又要重讲一遍”。

**B. 你做了什么（过程拆解）**
- 你第一版流程是什么？最粗糙也可以。  
- 你做出的最关键的 1–2 个设计决策是什么？  
- 哪一步你觉得“没有这一步就不成立”？

**C. 踩坑与调整（反向拆解）**
- 哪一段失败最明显？具体失败表现是什么？  
- 你尝试过的无效方案有哪些？为什么没用？  
- 最后是哪一次调整让它真正变好？

**D. 结果与证据（可验证）**
- 给一个“前后对比”的具体例子。  
- 你最认可的 1–2 个指标是什么？  
- 这套方法的边界是什么？什么场景会失效？

**E. 人的变化（强化真实感）**
- 这套流程对你个人最大的改变是什么？  
- 你最想对“过去那个自己”说的一句话是什么？

Only proceed after user confirmation (e.g., “可以/开始/就按这个写”).

## Multi-Phase Output Contract

This skill must be run in distinct phases:

1. Generate `00_brief.md`, then stop.
2. Generate WeChat article (with section subtitles), then stop.
3. Generate `wechat_notes.md` (WeChat image plan + prompts), then stop.
4. Generate **only the first** WeChat image prompt/image; run QA loop until pass, then stop (wait for “风格OK/继续”).
5. Generate remaining WeChat images/prompts; run QA loop per image; then update `wechat_article.md` with image placement markers, then stop.
6. Generate XHS storyboard, then stop.
7. Generate **only the first** XHS image prompt/image; run QA loop until pass, then stop (wait for “风格OK/继续”).
8. Generate remaining XHS images/prompts with QA loop and complete `xhs_post.md`, then stop.

Do not produce both drafts in a single conversational response. The split is mandatory.

## Length Gates (Hard Rules)

- WeChat article: 2400–2600 Chinese characters (target ~2500).
- Xiaohongshu caption: at least 500 Chinese characters (recommended 500–700).
- Each Xiaohongshu image: 1 headline + 2–4 short bullet points.

If a draft is under-length, expand before saving the file.

## WeChat Article Rules

**核心原则：让读者跟着经历走，自己产生感受，而不是被教育。**

**叙事结构（优先使用）：**
- 从一个具体的时间点或场景切入，不要从"宏大背景"开头
- 按时间线或因果链推进，在经历中自然带出观点
- 结尾点到为止，不做总结，不升华，不说"这说明了什么"
- 允许思路有跳跃感，不需要每段都有完美的过渡句

**禁止使用"教程框架"：**
- ❌ 开头痛点 → 中间方案 → 结尾升华（这是 AI 的默认模板）
- ❌ 能做什么 → 在哪做 → 能带来什么改变（这是说明书结构）
- ❌ 结尾用金句总结规律，比如"如果你不能……那再强的模型也只是黑盒"
- ❌ 把经历包装成完美成功案例，夸大成果

**关于小标题：** 可以用，标题要是"这件事叫什么"，不是"这件事说明了什么道理"。

- Allow variants: "观点短论" or "清单干货" when the topic fits better.
- Keep paragraphs short, avoid overly academic tone.
- Use clear section subtitles to improve scanability; let the model decide the count based on content density.
- Include 2–4 scannable lists.
- End with a **tight summary /收束** (no marketing CTA).  
  - 2–4 sentences，回到开头的困境与变化  
  - 可以留一个问题，但不引导"关注/评论/私信/领取"  
  - 不做夸大承诺，不用模板式鸡汤
- WeChat images can be photo/illustration/diagram based on tone; do not force Q-style.
- Ensure the main body length meets the 2400–2600 character gate.
- Output file should start with the title, then a ~30字简介, then正文; no metadata block.
- Apply the voice constraints defined in `references/my_voice.md` by default. This is your highest priority.
  - 长短句结合、有节奏
  - 允许连接词：所以/但是/因为/比如/结果
  - 避免：然而/因此/基于/催生/驱动
  - 不新增原文未提内容或案例
  - 保持口语化与原用词习惯

## WeChat Image Rules

- Provide 1 cover image + 4–6 WeChat insert images by default.
- Aspect ratio: **4:3 landscape** for all WeChat images.
- Cover image (hard rule): **use Q-style main character**, theme-aligned, and **must be text-free** (no title/subtitle/labels/numbers/letters/watermark/logo).
  - Add an explicit negative constraint in prompts: `no text, no typography, no letters, no numbers, no watermark, no logo`.
- For WeChat cover prompts, do **not** specify any on-image text; if a draft includes an “On-image text” field for the cover, delete it and rewrite the prompt as text-free.
- Insert images can be **flexible style** (photo / illustration / diagram), but **must be consistent within the same article**.
- Define **one visual style baseline** per material and apply it to all WeChat + XHS images (color palette, line weight, lighting, texture, character treatment).
- Record this style baseline in `wechat_notes.md` and reuse it verbatim in every later image prompt.
- WeChat images should be **light on text**, but **not text-free** when the image is a flow/diagram/structure.
- If image type is **diagram/flow/architecture**, include **short labels** (2–6 words) on nodes/steps.
- Avoid generic icon-only images without labels; require visual + label pairing for meaning.
- Avoid “PPT icon” look: no flat template cards, no generic UI boxes; prefer illustrated scenes or soft infographic with texture.
- For each image: specify placement (section), intent, and recommended style (photo/illustration/diagram).
- Include prompts for each image; only use Q-style character if it fits the tone.

For structure variants, read `references/workflow.md`.
For voice and phrasing patterns, read `references/voice.md`.

## Xiaohongshu Storyboard Rules

- Use an image-first narrative: cover → why → before/after → workflow → tools → results → reflection/CTA.
- Keep the main character consistent across images.
- Each image should include 1 headline + 2–4 short points.
- Favor high-contrast numbers or short metrics in at least 2 images.
- Aspect ratio: **9:16 portrait** (mobile full-screen) for all XHS images.
- Do **not** print aspect-ratio labels on the image (e.g., “9:16版/竖图版/比例:9:16”).
- Reuse the exact same style baseline defined in `wechat_notes.md`; do not introduce new style families in XHS prompts.
- Ensure caption length is 500+ characters.

## Xiaohongshu Caption Rules

- Mirror the WeChat narrative arc in a compressed form: hook → problem framing → method/workflow → results → reflection/收束.
- Keep paragraphs short; include 1 scannable micro-list (3–5 bullets) max.
- End tight (2–3 sentences). You may leave 1 question, but avoid marketing CTAs (no “关注/评论/私信/领取”).
- Apply the “去 AI 味” constraints by default (same as WeChat rules).

For visual rules and layout guidance, read `references/xhs_visual.md`.

## Character Consistency Rules

- Use portrait photos as the **identity anchor** when making a “main character”.
  - Preferred location (workspace): `inputs/images/portraits/`
  - Alternative (inside this skill): `assets/portraits/`
- 在图像中保持主角相同的发型、脸型。
- Do not require a literal consistent human character every time: allow “character variants” (e.g., a hoodie mascot / one recognizable feature / symbolic object) as long as it keeps recognizable continuity.
- Keep the overall style pack consistent across images in the same material (palette/texture/line weight).

## Image Prompt Format

For each image, output:

- Scene intent
- On-image text (headline + bullets or short labels)
  - Required for Xiaohongshu images
  - Optional for WeChat insert images
  - Forbidden for WeChat cover images (cover must be text-free)
  - Do not include ratio/size labels as on-image text (e.g., “9:16版/3:4版/竖图版”)
  - **Whitelist rule (hard)**: only allow the exact text provided under “On-image text”; do not invent any extra corner labels such as “9:16版/移动端全屏报/竖图版”.
- Negative constraints (required for WeChat cover): `no text, no typography, no letters, no numbers, no watermark, no logo`
- Composition and props
- Character description (refer to portrait assets)
- Style keywords (include the shared **style pack** for this article)
- Aspect ratio
- Coze prompt (final executable prompt)
- QA checklist result (pass/fail + reason + retry count)

## Coze API (optional)

If the user wants automatic image generation via Coze, use the local script:

```bash
python3 ~/.codex/skills/wechat-xhs-content/scripts/coze_generate.py "your prompt"
```

For this project, always attach a random portrait reference (unless the user explicitly says not to) and initialize one dedicated session id per material:

```bash
COZE_SESSION_ID="$(uuidgen | tr '[:upper:]' '[:lower:]' | tr -d '-')" \
python3 ~/.codex/skills/wechat-xhs-content/scripts/coze_generate.py "your prompt" --ref-image auto --no-run-id
```

For consistency across multiple images in the same material:

- Reuse the same `COZE_SESSION_ID` for the whole material (do not pass `--new-session` for every single image).
- Pin the portrait reference:
  - Easiest: run once with `--ref-image auto`, then reuse the printed portrait path for later images; or
  - Set `COZE_REF_IMAGE=/absolute/or/workspace/relative/path.jpg` (so `--ref-image auto` always uses that portrait); or
  - Set a stable `COZE_SESSION_ID` (the script deterministically picks a portrait based on session id).

To guarantee a consistent visual style across different topics, prepend the global style lock **and** apply the correct platform lock (to avoid wrong aspect ratios / unwanted “9:16版” labels):

- WeChat cover (4:3 landscape, **no text**):

```bash
python3 ~/.codex/skills/wechat-xhs-content/scripts/coze_generate.py "your prompt" \\
  --profile wechat_cover --ref-image auto --no-run-id
```

- Xiaohongshu pages (9:16 portrait, **only allow the provided On-image text**):

```bash
python3 ~/.codex/skills/wechat-xhs-content/scripts/coze_generate.py "your prompt" \\
  --profile xhs --ref-image auto --no-run-id
```

The script reads `COZE_API_TOKEN` from the environment, or prompts once per run.
It also loads `~/.codex/skills/wechat-xhs-content/.env` / `.env.local` if present.

Image filename controls (optional env vars):

- `COZE_IMAGE_PREFIX` (e.g., `wechat_cover`, `wechat_insert`, `xhs`)
- `COZE_IMAGE_SEQ_START` (default `1`)
- `COZE_IMAGE_PAD` (default `2`, e.g., `01`, `02`)
- `COZE_IMAGE_INCLUDE_RUN_ID` (default `1`; set to `0` for clean `xhs_01` style names)
- `COZE_IMAGE_RUN_ID` (optional fixed run id)
- `COZE_MIN_IMAGE_BYTES` (default `50000`)
- `COZE_SAVE_RAW` (set to `1` to save small/invalid responses into `outputs/archive/invalid_outputs`)

Example (XHS ordered images):

```bash
COZE_IMAGE_PREFIX=xhs COZE_IMAGE_SEQ_START=1 COZE_IMAGE_PAD=2 COZE_IMAGE_INCLUDE_RUN_ID=0 \\
python3 ~/.codex/skills/wechat-xhs-content/scripts/coze_generate.py "prompt" --profile xhs
```

Save into a specific material folder:

```bash
python3 ~/.codex/skills/wechat-xhs-content/scripts/coze_generate.py "prompt" --out-dir "outputs/wechat/YYYYMMDD_HHMMSS_<素材名>/images"
```

First-image-only rule (hard):

- When generating images (WeChat or XHS), generate **only the first image** first, show it to the user, and wait for “风格OK/继续” before generating the rest.

## Automated QA Script (recommended)

Use this wrapper to run generation + AI image QA + fail-delete-regenerate in one loop:

```bash
python3 ~/.codex/skills/wechat-xhs-content/scripts/coze_generate_with_qa.py "your prompt" \
  --profile xhs \
  --out-dir "outputs/xhs/YYYYMMDD_HHMMSS_<素材名>/images" \
  --prefix xhs \
  --seq 1 \
  --ref-image auto \
  --qa-platform xhs \
  --allowed-text-file "/absolute/path/to/on_image_text.txt"
```

For WeChat cover no-text QA:

```bash
python3 ~/.codex/skills/wechat-xhs-content/scripts/coze_generate_with_qa.py "your prompt" \
  --profile wechat_cover \
  --out-dir "outputs/wechat/YYYYMMDD_HHMMSS_<素材名>/images" \
  --prefix wechat_cover \
  --seq 1 \
  --ref-image auto \
  --qa-platform wechat \
  --require-no-text
```

Hard behavior of this wrapper:

- QA fails => delete failed image file immediately and regenerate same index.
- Max retries per image default: 3 (configurable).
- Requires `OPENAI_API_KEY` for AI visual QA.

## Unified Style Lock (Hard Rule)

- Use one unified style lock chain for both platforms:
  - Base lock: `references/global_style_lock.txt`
  - Platform lock: WeChat uses `wechat_cover` or `wechat_insert`; XHS uses `xhs`
- Platform locks can only control ratio/text rules. They must not override the material style baseline.
- Keep style words stable across all images of one material. Do not switch to another style family mid-run.
- Keep the same portrait identity anchor and same `COZE_SESSION_ID` across all images in one material.

## Image QA + Regeneration Loop (Hard Rule)

Run this loop for **every** generated image (WeChat and XHS):

1. Check image against hard requirements:
   - Ratio is correct (WeChat 4:3, XHS 9:16).
   - Text policy is correct (cover no-text, XHS text whitelist only, no ratio labels).
   - No watermark/logo/二维码/角标。
   - Character consistency is preserved (face/hair/silhouette).
   - Style baseline remains consistent (palette/line weight/lighting/texture).
2. If failed:
   - Delete the failed file immediately (`rm -f <failed_image_path>`).
   - Tighten prompt constraints and regenerate the **same image index**.
   - Retry until pass (max 3 retries per image).
3. If still failing after 3 retries:
   - Stop and ask user to adjust direction before continuing.

Only keep passed images in the material `images/` folder; do not keep failed drafts.

Optional env overrides:

- `COZE_STREAM_URL` (default: https://vttznq9qz8.coze.site/stream_run)
- `COZE_RUN_URL` (default: https://vttznq9qz8.coze.site/run)
- `COZE_WORKFLOW_ID` (recommended for coze.cn)
- `COZE_PROJECT_ID` and `COZE_SESSION_ID` (legacy stream_run payload)
- `COZE_USE_STREAM` (set to 0 to force non-stream)

If `COZE_WORKFLOW_ID` is set, also set `COZE_STREAM_URL=https://api.coze.cn/v1/workflow/stream_run` unless you have a custom proxy.

### Gemini Flow Workflow (/run) mode

If you deployed a minimal Gemini Flow workflow that exposes `POST /run` with body `{ "text": "...", "reference_image": { "url": "...", "file_type": "image" } }`,
set these env vars (in the skill `.env.local`) so **any new chat** can call it directly without agent prompt drift:

- `COZE_SIMPLE_WORKFLOW=1`
- `COZE_RUN_URL=https://<your>.coze.site/run`
- Optional defaults:
  - `COZE_PROMPT_PREFIX_FILE=/Users/wali/.codex/skills/wechat-xhs-content/references/global_style_lock.txt`
  - `COZE_REF_IMAGE_DEFAULT=inputs/images/portraits/<your>.jpg` (fixed) or `COZE_REF_IMAGE_DEFAULT=auto` (random pick)
  - When using `auto`, the script samples from `inputs/images/portraits/` by default. To include skill portraits too: `COZE_REF_IMAGE_AUTO_INCLUDE_SKILL=1`.

Then you can run `coze_generate.py` without passing `--prompt-prefix-file` / `--ref-image` every time; it will pick them from env.

Reference portrait (for character consistency)

Option A: legacy proxy `/stream_run` (no workflow needed)

```bash
# Randomly attach one portrait from inputs/images/portraits/ into the prompt payload.
python3 ~/.codex/skills/wechat-xhs-content/scripts/coze_generate.py "prompt" --ref-image auto --no-run-id
```

Option B: official coze.cn workflow API (recommended when you control inputs)

```bash
# In your Coze workflow, define an input key (default expected: PORTRAIT) of type image/file.
COZE_WORKFLOW_ID=... COZE_STREAM_URL=https://api.coze.cn/v1/workflow/stream_run \\
python3 ~/.codex/skills/wechat-xhs-content/scripts/coze_generate.py "prompt" --ref-image "inputs/images/portraits/your.jpg" --ref-param PORTRAIT
```

For workflows, the script uploads the file via `COZE_FILES_UPLOAD_URL` (default: `https://api.coze.cn/v1/files/upload`) and passes `{ "file_id": "..." }` into the workflow parameters.

## Files in This Skill

- `inputs/images/portraits/` (workspace) or `assets/portraits/` (skill): Source portrait photos for Q-style character consistency
- `scripts/coze_generate_with_qa.py`: Generation + AI QA + fail-delete-regenerate loop
- `references/samples.md`: Available sample content pointers
- `references/voice.md`: Voice and tone patterns
- `references/workflow.md`: Structure templates and variants
- `references/xhs_visual.md`: Visual layout and storyboard guidance
