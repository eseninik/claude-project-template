"""Parallel voice transcription worker. Usage: python transcribe_worker.py <worker_id> <total_workers>"""
import os, sys, re
from pathlib import Path

ffmpeg_bin = r'C:\Users\Lenovo\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin'
os.environ['PATH'] = ffmpeg_bin + ';' + os.environ['PATH']

worker_id = int(sys.argv[1])
total_workers = int(sys.argv[2])

voice_dir = Path(r'C:\Users\Lenovo\Downloads\Telegram Desktop\ChatExport_2026-03-18\voice_messages')
output_dir = Path(r'C:\Bots\Migrator bots\claude-project-template-update\work')

# Get all March files sorted
all_files = sorted([f for f in voice_dir.glob('*.ogg') if '-03-2026' in f.name])
# Split across workers
my_files = [f for i, f in enumerate(all_files) if i % total_workers == worker_id]

print(f'Worker {worker_id}: {len(my_files)} files to process', flush=True)

from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')
print(f'Worker {worker_id}: turbo model loaded', flush=True)

results = []
for i, f in enumerate(my_files):
    m = re.search(r'@(\d{2})-(\d{2})-(\d{4})_(\d{2})-(\d{2})-(\d{2})', f.name)
    if m:
        day, month, year, h, mi, s = m.groups()
        date_str = f'{year}-{month}-{day} {h}:{mi}'
    else:
        date_str = 'unknown'

    try:
        segments, info = model.transcribe(str(f), language='ru', beam_size=3, vad_filter=True)
        text = ' '.join([seg.text.strip() for seg in segments])
        duration = round(info.duration, 1)
    except Exception as e:
        text = f'[ERROR: {e}]'
        duration = 0

    results.append(f'### {f.name}\n**Date:** {date_str}\n**Duration:** {duration}s\n**Text:** {text}\n')
    print(f'Worker {worker_id}: [{i+1}/{len(my_files)}] {f.name} ({duration}s)', flush=True)

# Save worker results
out_file = output_dir / f'voice_part_{worker_id}.md'
out_file.write_text('\n'.join(results), encoding='utf-8')
print(f'Worker {worker_id}: DONE -> {out_file}', flush=True)
