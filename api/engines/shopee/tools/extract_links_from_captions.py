#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract links from captions/posts to create a file for affiliate conversion.
Supports both new pipeline (post.txt) and old pipeline (caption.txt) structures.

Creates: _links_to_convert.txt with one link per line

Usage:
    python extract_links_from_captions.py [date_or_folder]
"""

import sys
import re
import io
from pathlib import Path
from datetime import datetime

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def find_ready_to_post_dir(date_str):
    """Find the ready_to_post directory for a given date."""
    # New pipeline structure: ready_to_post/{date}/
    candidates = [
        Path(f"shopee_affiliate/data/ready_to_post/{date_str}"),
        Path(f"data/ready_to_post/{date_str}"),
        # Old pipeline structure: 05_ReadyToPost/{date}/
        Path(f"shopee_affiliate/data/05_ReadyToPost/{date_str}"),
        Path(f"data/05_ReadyToPost/{date_str}"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def extract_shopee_link(text):
    """Extract first Shopee link from text."""
    links = re.findall(r'https://shopee\.co\.th/[^\s\)\'"]+', text)
    return links[0] if links else None


def extract_links(date_str=None, output_dir=None):
    """Extract links from all post.txt/caption.txt files in a date folder."""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    base_dir = find_ready_to_post_dir(date_str) if not output_dir else Path(output_dir)

    if not base_dir or not base_dir.exists():
        print(f"❌ ไม่พบโฟลเดอร์สำหรับวันที่: {date_str}")
        print(f"   ลองหาใน: shopee_affiliate/data/ready_to_post/{date_str}")
        return False, []

    print(f"📂 สแกน {base_dir} เพื่อหาลิงก์...\n")

    links_with_paths = []  # list of (link, post_file_path)

    # New pipeline: each subdirectory has post.txt
    post_files = list(base_dir.rglob("post.txt"))
    # Old pipeline: each time-slot subdir has caption.txt
    caption_files = list(base_dir.rglob("caption.txt"))

    all_files = sorted(post_files + caption_files, key=lambda p: str(p))

    if not all_files:
        print(f"❌ ไม่พบ post.txt หรือ caption.txt ใต้ {base_dir}")
        return False, []

    for f in all_files:
        content = f.read_text(encoding='utf-8', errors='replace')
        link = extract_shopee_link(content)
        if link:
            links_with_paths.append((link, str(f)))
            print(f"✅ {f.parent.name}/{f.name}: {link[:60]}...")
        else:
            print(f"⚠️  {f.parent.name}/{f.name}: ไม่พบลิงก์ Shopee")

    if not links_with_paths:
        print(f"\n❌ ไม่พบลิงก์เลย")
        return False, []

    # Save links to _links_to_convert.txt
    links_file = base_dir / "_links_to_convert.txt"
    with open(links_file, 'w', encoding='utf-8') as f:
        for link, path in links_with_paths:
            f.write(link + '\n')

    print(f"\n✅ บันทึก {len(links_with_paths)} ลิงก์ไปที่: {links_file}")
    return True, [lp[0] for lp in links_with_paths]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract Shopee links from post/caption files")
    parser.add_argument("date", nargs="?", help="Date folder (YYYY-MM-DD), default: today")
    parser.add_argument("--dir", help="Override directory path")
    args = parser.parse_args()

    success, _ = extract_links(args.date, args.dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
