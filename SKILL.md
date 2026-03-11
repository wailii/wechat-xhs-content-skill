---
name: "wechat-xhs-content"
description: "Create staged WeChat public account articles and Xiaohongshu posts with clarifying Q&A, material extraction, WeChat article drafting, WeChat image scene descriptions, and Xiaohongshu storyboard plus caption output. Use when the user asks for 公众号文章, 微信公众号内容, 小红书文案, XHS 图文, 配图描述, 图文分镜, or adapting one story for both channels. No direct image generation."
compatibility: "Claude.ai and Claude Code. Text drafting works without external APIs. Optional local helper scripts are included for folder setup."
metadata:
  author: "wali"
  version: "2026-03-10-format-routing-v2"
---

# WeChat + 小红书内容工作流（含体裁路由 + 认知核查）

## Quick Start

Follow this workflow every time unless the user requests a subset.

0. Create per-material folders under `outputs/wechat/` and `outputs/xhs/` (same `<material_id>`; see "Material Folder Rules").
1. Ask user to narrate freely — user always narrates in story form first, this is their natural mode.
2. Run Format Routing immediately after narration — judge best format, wait for user confirmation (see "Format Routing").
3. Run targeted follow-up questions based on the confirmed format (see "Clarifying Questions").
4. Run Cognitive Check during follow-up — flag factual errors or logical blind spots, wait for user clarification (see "Cognitive Check Rule").
5. Extract material + lock core stance, wait for user confirmation (see "Multi-Phase Output Contract").
6. If (and only if) the user explicitly provides a source document path, read it.
7. Draft WeChat article and save to `outputs/wechat/<material_id>/wechat_article.md`.
8. Stop and wait for user approval ("OK/继续/通过").
9. Draft WeChat image scenes and save to `outputs/wechat/<material_id>/image_prompts.md`.
10. Stop and wait for user approval ("OK/继续/通过").
11. Draft Xiaohongshu post and save to `outputs/xhs/<material_id>/xhs_post.md`.
12. If needed, iterate text only (no direct image generation in this skill).

---

## Format Routing（体裁路由）

### 执行时机

**用户完成第一次自由口述之后，立即执行体裁路由——在定向追问之前。**

用户永远以叙事方式口述，这是他们的自然状态，不要让用户在讲述前就想好体裁。先听完，再判断。

### 判断逻辑

根据用户提供的素材，沿以下决策树判断：

```
素材进来
  ├── 素材有具体的时间线、经历、踩坑 → [叙事体]
  ├── 素材核心是一个争议性命题，存在内在矛盾或两种声音 → [对话体]
  ├── 素材是一个工具/系统/工作流，需要剖开来讲清楚逻辑 → [拆解体]
  └── 素材是一个"如果……会怎样"的假设性问题，需要推演 → [思想实验体]
```

**遇到边界情况时（素材可能跨两种体裁）：**
- 把两种体裁都列出来，说明各自的侧重点，让用户选择
- 不能自行决定后直接写，必须得到用户确认

### 输出格式（必须执行）

判断完成后，输出一段说明，格式如下：

```
【体裁判断】
我判断这篇适合用「XX体」，原因是：[1-2句说明为什么这个素材适合这个体裁]

[如果是对话体，额外输出：]
角色搭档建议：
方案 A：[角色A] vs [角色B] — 核心张力：[一句话说明]
方案 B：[角色A] vs [角色B] — 核心张力：[一句话说明]
方案 C：[角色A] vs [角色B] — 核心张力：[一句话说明]

你确认用这个体裁吗？
```

等用户确认后，读取对应的 format 文件，再进入写作。

### 体裁对应的 Format 文件（Progressive Loading）

| 体裁 | 读取文件 |
|---|---|
| 叙事体 | `references/format_narrative.md` |
| 对话体 | `references/format_dialogue.md` |
| 拆解体 | `references/format_breakdown.md` |
| 思想实验体 | `references/format_thought_exp.md` |

**硬规则：** 每次只读一个 format 文件，对应用户确认的体裁。不要一次全部读入。

---

## Progressive Loading (Hard Rule)

Read only what is needed:

- Always read before any writing:
  - `references/my_voice.md`
  - `references/user_voice_sample.md`
  - `references/ai_taste_blacklist.md`
- Read when needed:
  - `references/samples.md` (if examples are needed)
  - `references/title_rules.md` (when generating title options)
  - `references/wechat_article_rules.md` (before drafting WeChat article — 叙事体专用，其他体裁用对应 format 文件替代)
  - `references/format_narrative.md` (叙事体，替代 wechat_article_rules.md)
  - `references/format_dialogue.md` (对话体，用户确认后读取)
  - `references/format_breakdown.md` (拆解体，用户确认后读取)
  - `references/format_thought_exp.md` (思想实验体，用户确认后读取)
  - `WeChat Image Prompt Rules` in this file (before drafting WeChat image prompts)
  - `references/xhs_rules.md` (before drafting XHS storyboard/caption)
  - `references/channel_adaptation.md` (only when user asks about 微信小绿书/小红书导入适配)

If there is any conflict between old legacy reference files and the rules in this SKILL + above new reference files, follow this SKILL and the above new reference files.

---

## Inputs to Ask For (keep brief)

Ask only when missing:

- Topic / material name (1 sentence; used for folder naming)
- Audience and desired outcome
- Any constraints (length, tone, deadlines)
- Clarifying Q&A required before writing (see "Clarifying Questions")

Assume defaults if not provided:

- Audience: AI-savvy product/knowledge workers
- WeChat length: determined by format file (varies by format type)
- Tone: Defined in `references/my_voice.md`. Must be conversational, personal, and avoid overly formal or "AI-like" language.
- XHS format: multi-image narrative + caption + tags (image count determined by content)
- XHS caption length: 200–400 字

---

## Deliverables

Always output in separate files with clean content only:

- WeChat draft (title + body only): `outputs/wechat/<material_id>/wechat_article.md`
- WeChat image scenes (6 images): `outputs/wechat/<material_id>/image_prompts.md`
- Xiaohongshu draft (storyboard + caption + hashtags): `outputs/xhs/<material_id>/xhs_post.md`

Only after writing files, provide a short response that lists the updated file paths.

---

## Stage Gates (Hard Rule)

- Gate A: After free narration, run format routing immediately — wait for user confirmation of format type. For dialogue format, also confirm role pair.
- Gate B: After targeted follow-up questions complete, wait for "开始/就按这个写/可以".
- Gate C: After material extraction + stance lock, wait for user confirmation of both extracted details and core stances.
- Gate D: After WeChat article, wait for "OK/继续/通过".
- Gate E: After `image_prompts.md`, wait for "OK/继续/通过".
- Gate F: After `xhs_post.md`, wait for "OK/继续/通过".

Do not proceed past a gate without explicit user confirmation.

---

## WeChat File Rules

- Only final article content: 标题 + 正文。
- 不要在开头输出元信息、流程标签、说明文字。
- 正文可以有小标题，但不要使用"第一部分/第二部分"这类模板标题。
- 不要包含任何生图提示词、配图计划或素材生成说明。

---

## WeChat Image Prompt Rules

- 必须读取已确认的 `wechat_article.md`，再生成配图描述。
- 输出文件：`outputs/wechat/<material_id>/image_prompts.md`。
- 固定 6 张图：封面（图1）+ 图2-图6（起点/第一个坑/最崩瞬间/转折复盘/结尾落点）。
- 每张图都要写：用途、情绪、场景描述（给 Gemini），并且是横图 16:9。
- 场景描述必须包含：角色情绪 + 动作/姿态 + 屏幕/道具内容 + 背景色调。
- 禁止泛描述（如"人在用电脑""人在思考""成功微笑完成任务"）。
- 图内文字用中文；产品名保留英文原名（OpenClaw、Kimi、CodeX、Claude 等）。
- 本阶段只生成场景描述，不直接生成图片。

---

## Xiaohongshu File Rules

- 包含图文分镜（每张图：场景描述 + 1 个标题 + 内容）。
- 包含小红书正文（200–400 字）和 hashtags。
- 不要包含任何生图提示词。
- 图文分镜中每张图的场景描述，最终会发给 Gemini 生成图片。描述要足够具体，包含情绪、动作、屏幕内容和道具。

Never combine WeChat and XHS drafts into a single file.

---

## Output Hygiene (Hard Rule)

- Always write into `outputs/wechat/<material_id>/` and `outputs/xhs/<material_id>/` only.
- Never write Markdown drafts directly under `outputs/` root.
- Ensure directories exist before writing.

---

## Source Document Policy

- Do not read any source document unless the user explicitly provides the file path.
- If no path is provided, proceed with questions only and do not assume a default document.

---

## Material Folder Rules (Hard Rule)

For every new topic/material, create a dedicated folder under both platform directories using the same `<material_id>`:

- WeChat root: `outputs/wechat/YYYYMMDD_HHMMSS_<素材名>/`
  - Files: `wechat_article.md`
  - Images: `outputs/wechat/<material_id>/images/` (optional; user-managed assets)
- XHS root: `outputs/xhs/YYYYMMDD_HHMMSS_<素材名>/`
  - Files: `xhs_post.md`
  - Images: `outputs/xhs/<material_id>/images/` (optional; user-managed assets)

Naming:

- `YYYYMMDD_HHMMSS` uses local time.
- `<素材名>` is a short human-readable name (Chinese ok). Strip `/\\:*?"<>|` and keep it <= 30 chars.

Optional helper:

- Create folders via `scripts/new_material.py "<素材名>"`

---

## Clarifying Questions（定向追问）

### 第一轮：永远只问一个问题

> 你能不能用说话的方式，把这件事从头跟我讲一遍？就像跟朋友聊天一样，不用整理，想到哪说到哪。讲完我再问你几个细节。

### 第二步：立即做体裁路由（见 Format Routing 章节）

不要在体裁确认之前就追问。先路由，再追问。

### 第三步：根据确认的体裁，定向追问缺失信息

追问数量没有上限，用户明确表示不会嫌烦，发现关键信息缺失就问，可以多轮。

**但每个体裁关注的信息不同：**

| 体裁 | 追问重点 |
|---|---|
| 叙事体 | 时间节点、情绪变化、具体细节（被跳过的"理所当然"的部分）、失败和没做好的地方 |
| 对话体 | 你内心的另一种声音是什么、让你真正动摇的论点在哪里、现在的判断是什么 |
| 拆解体 | 每个关键步骤的具体操作、遇到了什么问题、为什么这样设计而不是那样 |
| 思想实验体 | 这个假设的触发点是什么、推演到哪里会卡住、你自己最不确定的地方是哪里 |

**追问时注意挖"被跳过的细节"：**
用户习惯跳过自认为理所当然的部分。如果听到"然后就……"、"之后就……"，这里几乎一定有被省略的有画面感的细节，必须追问。

Only proceed to material extraction after user signals readiness (e.g., "可以/开始/就按这个写").

---

## Cognitive Check Rule（认知核查）— Hard Rule

### 什么时候触发

在定向追问阶段，如果发现用户陈述中存在以下情况，必须立即提出：

- **事实性错误**：用户描述的某个工具/产品/技术细节与实际情况不符
- **逻辑盲点**：用户的推理链条在某处有明显跳跃或漏洞，可能影响文章的可信度
- **与已知信息矛盾**：用户现在说的和之前说过的有明显冲突

### 怎么提出

用追问的方式，不是纠正的方式：

> "这里我有个疑问——[具体描述你发现的问题]。你当时的情况是不是……？"

等用户回应后重新确认，再继续。

### 什么时候不触发

- 用户有强立场和否定性判断：**不触发**，不需要"平衡"，立场是用户的，不是错误
- 用户的表达方式不够精确：**不触发**，这是语感问题，不是认知问题
- 用户对某件事有不满或批评：**不触发**，情绪和判断是真实的，不需要被纠正

**核心原则：只纠事实，不纠立场。**

---

## Multi-Phase Output Contract

This skill must be run in distinct phases:

1. **自由口述**：用户用说话的方式讲，不限方式，不限长度。
2. **体裁路由**：判断体裁并输出理由，如果是对话体同时给出角色搭档方案，等用户确认。
3. **定向追问**：根据确认的体裁，多轮追问缺失信息。追问过程中同时执行认知核查。
4. **素材提炼 + 立场锁定**（必做，写作前）：
   - 从用户回答中挑出 5–8 个最具体、最有画面感的句子或细节，列出来给用户确认
   - 同时单独列出用户的**核心立场**（尤其是否定性判断），让用户逐条确认
   - 给出 3 个候选标题
   - 等用户确认后才能进入写作
5. 读取对应的 format 文件（Progressive Loading 规则），然后 generate `wechat_article.md`，then stop.
6. **字数自检**（必做，保存前）：统计中文字数，目标字数见对应 format 文件。若不足，不允许自行扩写补字数，必须继续向用户追问补充素材，达标后再保存。
7. Generate `image_prompts.md`（必做，6 张公众号配图场景描述），then stop.
8. Generate `xhs_post.md` (storyboard + caption + hashtags, no direct image generation), then stop.
9. If user asks for revisions, iterate text only.

Do not produce both drafts in a single conversational response. The split is mandatory.

---

## Length Gates (Hard Rules)

- WeChat article: 见对应 format 文件（不同体裁有不同目标字数）。
- Xiaohongshu caption: 200–400 Chinese characters.
- Each Xiaohongshu image: scene description + 1 headline + content.

If a draft is under-length, do follow-up questioning first, then revise.

---

## Voice and Anti-AI Taste

- Dynamic blacklist: maintain `references/ai_taste_blacklist.md`; append terms user identifies as "AI味" and avoid them in future drafts.
- Auto-learning voice samples: append high-quality, non-duplicate user natural-speech samples to `references/user_voice_sample.md` silently.
- Do not collect short confirmations, commands, or low-signal text.
