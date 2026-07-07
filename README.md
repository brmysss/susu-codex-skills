# Susu Codex Skills

一组可复用的 Codex / Claude Code skills，用来把稳定的个人工作流沉淀成可分享、可迁移的 AI 工具。

## Skills

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
