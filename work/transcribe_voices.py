"""Transcribe March 2026 voice messages from Telegram chat export."""
import os
import sys
import re
import time
from pathlib import Path
from datetime import datetime

# Set ffmpeg path BEFORE importing faster_whisper
ffmpeg_bin = r"C:\Users\Lenovo\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin"
os.environ["PATH"] = ffmpeg_bin + os.pathsep + os.environ["PATH"]

from faster_whisper import WhisperModel

VOICE_DIR = Path(r"C:\Users\Lenovo\Downloads\Telegram Desktop\ChatExport_2026-03-18\voice_messages")
OUTPUT_FILE = Path(r"C:\Bots\Migrator bots\claude-project-template-update\work\voice_transcripts.md")
MARCH_PATTERN = re.compile(r"^(audio_\d+)@(\d{2})-03-2026_(\d{2})-(\d{2})-(\d{2})\.ogg$")


def parse_filename(fname):
    """Parse filename into (audio_id, datetime). Returns None if not March 2026."""
    m = MARCH_PATTERN.match(fname)
    if not m:
        return None
    audio_id = m.group(1)
    day, hour, minute, second = m.group(2), m.group(3), m.group(4), m.group(5)
    dt = datetime(2026, 3, int(day), int(hour), int(minute), int(second))
    return audio_id, dt


def main():
    # Collect March 2026 files
    files = []
    for f in VOICE_DIR.iterdir():
        parsed = parse_filename(f.name)
        if parsed:
            audio_id, dt = parsed
            files.append((dt, audio_id, f))

    files.sort(key=lambda x: x[0])
    print(f"Found {len(files)} March 2026 voice messages")

    # Load model
    print("Loading Whisper model (small, cpu, int8)...")
    model = WhisperModel("small", device="cpu", compute_type="int8")
    print("Model loaded.")

    # Transcribe
    results = []
    for i, (dt, audio_id, filepath) in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {filepath.name} ...", end=" ", flush=True)
        t0 = time.time()
        try:
            segments, info = model.transcribe(
                str(filepath),
                beam_size=5,
                language=None,  # auto-detect
                vad_filter=True,
            )
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
            text = " ".join(text_parts)
            duration = info.duration
            lang = info.language
            elapsed = time.time() - t0
            print(f"OK ({elapsed:.1f}s, {duration:.0f}s audio, lang={lang})")
        except Exception as e:
            text = f"[TRANSCRIPTION ERROR: {e}]"
            duration = 0
            lang = "?"
            print(f"ERROR: {e}")

        # Format filename part for header
        fname_stem = filepath.stem  # audio_N@DD-MM-YYYY_HH-MM-SS
        date_str = dt.strftime("%Y-%m-%d %H:%M")

        results.append({
            "header": fname_stem,
            "date_str": date_str,
            "duration": duration,
            "text": text,
            "lang": lang,
            "dt": dt,
        })

    # Write output
    print(f"\nWriting results to {OUTPUT_FILE} ...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("# Voice Transcripts — March 2026\n\n")
        out.write(f"Total: {len(results)} voice messages\n\n")
        out.write("---\n\n")
        for r in results:
            out.write(f"### {r['header']}\n")
            out.write(f"**Date:** {r['date_str']}\n")
            out.write(f"**Duration:** {r['duration']:.0f}s\n")
            out.write(f"**Text:** {r['text']}\n\n")

    print(f"Done! {len(results)} transcripts written.")


if __name__ == "__main__":
    main()
