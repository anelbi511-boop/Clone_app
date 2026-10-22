# Clone App — Independent Phase 1 Video MVP

Independent implementation, **not** proprietary HL Studio code.

## What works
- Browser UI, local Python HTTP server
- Upload JPG/PNG/WebP images and MP4/MOV/WebM videos (max 100MB per file)
- Create/select/save project with a list of uploaded media IDs
- Export a sequential 1280x720, 25 fps, silent MP4 using FFmpeg. Each image lasts 1-10 seconds; uploaded videos keep their duration. No transitions or audio yet.
- GitHub Actions runs Python tests on Windows; **Actions does not launch or publish this server.**

## Running on Windows
1. Install Python 3.10+ and FFmpeg, ensure both commands work in CMD: `python --version` and `ffmpeg -version`.
2. Download repository ZIP from GitHub (Code > Download ZIP), extract it.
3. In CMD inside repository root: `python backend\server.py`
4. Open `http://127.0.0.1:8790` in the browser.
5. Select/create a project, import media, then export MP4. Files are stored under `data/` locally (gitignored).

## Limitations
- Media file validation currently checks extension and upload size, not full file content; only import files you trust.
- Export runs synchronously and may take time; no progress or cancellation yet.
- Imported video audio is stripped. No timeline editor, AI, voice, C# launcher or ready-to-install EXE yet.
- Backend is localhost only; do not expose it to the public Internet.
- Some codecs may require an FFmpeg build with libx264.

## CI
`.github/workflows/ci.yml` runs `python -m pytest tests -q` on Windows.
