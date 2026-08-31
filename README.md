# Susu Codex Skills

一组可复用的 Codex / Claude Code skills，用来把稳定的个人工作流沉淀成可分享、可迁移的 AI 工具。

## Skills

### fact-opinion-judgment

对文章、社交媒体内容、音视频转写稿或用户提供的文本做“事实和观点判断”：逐条拆出事实性断言、观点、立场、行动建议、论据和隐含假设，并列出名词、动词、形容词、副词及评价/模态词；用户要求时，还会生成带原文高亮、点击浮窗和分析表格的自包含 HTML 报告。当前 Skill 版本为 `v0.3.2`。

它适合：

- 区分原文中的事实性断言、观点、解释和行动建议
- 检查观点背后的论据、论证、假设与证据缺口
- 分析作者如何通过词性、评价词、模态词和范围词表达立场
- 处理网页文章、X/论坛内容、音视频转写稿和本地 Markdown
- 生成可离线打开的原文标注页与结构化分析表格，并支持配置页底博客/站点主页入口

路径：

```text
skills/fact-opinion-judgment/
```

HTML 输出的数据接口、交互和版本规则见：

```text
skills/fact-opinion-judgment/references/html-output.md
```

可分发包：[fact-opinion-judgment.skill](fact-opinion-judgment.skill)

### bilibili-video-note

把 B 站或其他在线视频链接处理成离线图解笔记、结构化学习笔记和长图切片。

它适合：

- B 站视频图解笔记
- 课程/访谈/评论视频的结构化学习笔记
- 由 SRT 或转写稿继续生成图解长文
- 带来源、二维码、审计记录的可复盘内容产物

路径：

```text
skills/bilibili-video-note/
```

核心产物：

```text
video-note-output/
├── index.html
├── page.png
├── structured-note.md
├── slices/
├── media/
├── transcript/
└── audit/
```

## Install

把某个 skill 目录复制到本地 Codex skills 目录，例如：

```bash
cp -R skills/bilibili-video-note ~/.codex/skills/
```

然后在 Codex 中这样调用：

```text
$bilibili-video-note https://www.bilibili.com/video/BVxxxxxx/
```

## Requirements

`bilibili-video-note` 会按任务需要调用这些工具：

- `yt-dlp`
- `ffmpeg` / `ffprobe`
- Whisper 或可用的转写服务
- Chrome / Playwright，用于渲染 HTML 长图
- Python 3

对于 B 站视频，建议本机浏览器已登录 B 站，以便 `yt-dlp --cookies-from-browser chrome` 能读取登录态。公开视频有时也可能触发风控，需要重试或改用 API 元数据回退。

## Prompt

如果你只想在其他 AI 里复用“结构化笔记”的思路，可以直接复制：

[prompts/structured-video-note.prompt.md](prompts/structured-video-note.prompt.md)

## License

MIT
