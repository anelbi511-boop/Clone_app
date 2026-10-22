# Clone App — Independent MVP

A clean-room desktop-video-studio starter, not a copy of proprietary application assets or licensing code.

## Run locally

```bat
cd /d D:\ReverseLab\clone
python backend\server.py
```

Open http://127.0.0.1:8790 in your browser.

## Current scope
- Local HTTP server
- Create/list project metadata
- Web interface
- CI tests on Windows

## Not implemented yet
- Media upload/processing
- Timeline editor
- MP4 rendering
- C# WebView2 launcher
- AI services

## Next engineering tasks
1. Add secure media import and local file storage.
2. Create FFmpeg worker with job progress, cancellation and tests.
3. Add Windows launcher with WebView2 once backend is stable.
4. Add timeline and voice features independently.

Do not commit original application binaries, compiled private modules, private models, API keys, or third-party assets without permissions.
