"""Parse Telegram chat export HTML and extract March 2026 messages."""

import re
from pathlib import Path
from datetime import datetime

HTML_PATH = Path(r"C:\Users\Lenovo\Downloads\Telegram Desktop\ChatExport_2026-03-18\messages.html")
OUTPUT_PATH = Path(r"C:\Bots\Migrator bots\claude-project-template-update\work\text_messages.md")

html = HTML_PATH.read_text(encoding="utf-8")

# Split into message blocks
# Each message starts with <div class="message ...
# Classes can be: "message default clearfix", "message default clearfix joined", "message service"
msg_pattern = re.compile(
    r'<div\s+class="message\s+(default|service)\s*[^"]*"\s+id="(message-?\d+)"',
    re.DOTALL,
)

# Find all message div start positions
msg_starts = [(m.start(), m.group(1), m.group(2)) for m in msg_pattern.finditer(html)]

# Extract blocks
blocks = []
for i, (start, mtype, mid) in enumerate(msg_starts):
    end = msg_starts[i + 1][0] if i + 1 < len(msg_starts) else len(html)
    blocks.append((mtype, mid, html[start:end]))

# Track current date header and current sender
current_date_str = None
current_sender = None
march_started = False
messages = []

for mtype, mid, block in blocks:
    # Service messages contain date headers
    if mtype == "service":
        date_match = re.search(r'<div class="body details">\s*\n?(.*?)\s*</div>', block, re.DOTALL)
        if date_match:
            date_text = date_match.group(1).strip()
            # Check if it's a date like "9 March 2026"
            try:
                parsed = datetime.strptime(date_text, "%d %B %Y")
                current_date_str = parsed.strftime("%Y-%m-%d")
                if parsed.year == 2026 and parsed.month >= 3:
                    march_started = True
            except ValueError:
                pass
        continue

    if not march_started:
        continue

    # Extract datetime from title attribute
    date_match = re.search(r'title="(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2})', block)
    if not date_match:
        continue

    dt = datetime.strptime(date_match.group(1), "%d.%m.%Y %H:%M:%S")

    # Filter: only March 2026 onwards
    if dt.year < 2026 or (dt.year == 2026 and dt.month < 3):
        continue

    date_str = dt.strftime("%Y-%m-%d")
    time_str = dt.strftime("%H:%M")

    # Check if this is a "joined" message (continuation from same sender)
    is_joined = "joined" in block[:200]

    # Extract sender
    sender_match = re.search(r'<div class="from_name">\s*\n?(.*?)\s*</div>', block, re.DOTALL)
    if sender_match:
        raw_sender = sender_match.group(1).strip()
        if "Denis" in raw_sender:
            current_sender = "Denis"
        elif "Nikita" in raw_sender:
            current_sender = "Nikita"
        else:
            current_sender = raw_sender
    # If joined and no from_name, keep current_sender

    # Detect media types
    media_notes = []
    if "media_voice_message" in block:
        # Extract duration if present
        dur_match = re.search(r'<div class="details">\s*\n?\s*(\d+:\d+)', block)
        dur = f" ({dur_match.group(1)})" if dur_match else ""
        media_notes.append(f"[Voice message{dur}]")
    if "photo_wrap" in block:
        media_notes.append("[Photo]")
    if "media_video" in block and "video_file" in block:
        media_notes.append("[Video]")
    if "media_file" in block and "media_voice_message" not in block:
        # Check for sticker or file
        if "sticker" in block.lower():
            media_notes.append("[Sticker]")
        else:
            fname_match = re.search(r'<div class="details">\s*\n?\s*([^<]+)', block)
            if fname_match:
                media_notes.append(f"[File: {fname_match.group(1).strip()}]")
            else:
                media_notes.append("[File]")
    if "media_contact" in block:
        media_notes.append("[Contact shared]")
    if "media_location" in block:
        media_notes.append("[Location]")

    # Extract text
    # The text div - get the LAST one or the main one
    # Be careful: there can be text in nested elements
    text_matches = list(re.finditer(r'<div class="text">\s*\n?(.*?)\s*</div>', block, re.DOTALL))

    text_content = ""
    if text_matches:
        # Usually the last text div is the message text
        raw_text = text_matches[-1].group(1).strip()
        # Convert HTML to plain text
        # Replace <br> with newlines
        raw_text = re.sub(r'<br\s*/?>', '\n', raw_text)
        # Remove HTML tags but keep content
        raw_text = re.sub(r'<[^>]+>', '', raw_text)
        # Decode HTML entities
        raw_text = raw_text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
        text_content = raw_text.strip()

    # Build message content
    parts = []
    if media_notes:
        parts.append(" ".join(media_notes))
    if text_content:
        parts.append(text_content)

    if not parts:
        continue

    full_text = "\n".join(parts)
    messages.append((date_str, time_str, current_sender or "Unknown", full_text))

# Write output
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(f"# Telegram Chat: Denis Kazmin | Migrator — March 2026\n\n")
    f.write(f"Extracted {len(messages)} messages from {HTML_PATH.name}\n\n---\n\n")

    current_day = None
    for date_str, time_str, sender, text in messages:
        if date_str != current_day:
            current_day = date_str
            f.write(f"\n## {current_day}\n\n")

        f.write(f"### {date_str} {time_str} — {sender}\n")
        f.write(f"{text}\n\n")

print(f"Done! Extracted {len(messages)} messages to {OUTPUT_PATH}")
