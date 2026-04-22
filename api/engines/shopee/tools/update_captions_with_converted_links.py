#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update post.txt/caption.txt with converted affiliate links.
Supports both new pipeline (post.txt) and old pipeline (caption.txt) structures.

Usage:
    python update_captions_with_converted_links.py [date] [--input _converted_links.txt]
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
    candidates = [
        Path(f"shopee_affiliate/data/ready_to_post/{date_str}"),
        Path(f"data/ready_to_post/{date_str}"),
        Path(f"shopee_affiliate/data/05_ReadyToPost/{date_str}"),
        Path(f"data/05_ReadyToPost/{date_str}"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def update_captions(date_str=None, links_file="_converted_links.txt", output_dir=None):
    """Update post.txt/caption.txt files with converted affiliate links."""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    base_dir = find_ready_to_post_dir(date_str) if not output_dir else Path(output_dir)

    if not base_dir or not base_dir.exists():
        print(f"❌ ไม่พบโฟลเดอร์สำหรับวันที่: {date_str}")
        return False

    # Find converted links file
    links_path = base_dir / links_file
    if not links_path.exists():
        print(f"❌ ไม่พบไฟล์ลิงก์: {links_path}")
        print(f"   กรุณารัน convert_affiliate_links.py ก่อน")
        return False

    # Read converted links
    converted_links = [
        line.strip() for line in links_path.read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.startswith('#')
    ]

    if not converted_links:
        print(f"❌ ไม่พบลิงก์ใน {links_path}")
        return False

    print(f"📂 กำลังอัปเดตไฟล์ใน {base_dir}\n")

    # Find all post.txt and caption.txt files
    post_files = sorted(base_dir.rglob("post.txt"), key=lambda p: str(p))
    caption_files = sorted(base_dir.rglob("caption.txt"), key=lambda p: str(p))
    all_files = post_files + caption_files

    if not all_files:
        print(f"❌ ไม่พบไฟล์ post.txt หรือ caption.txt")
        return False

    updated_count = 0
    for idx, f in enumerate(all_files):
        content = f.read_text(encoding='utf-8', errors='replace')

        # Find original Shopee link
        shopee_links = re.findall(r'https://shopee\.co\.th/[^\s\)\'"]+', content)
        if not shopee_links:
            print(f"⚠️  {f.parent.name}/{f.name}: ไม่พบลิงก์ Shopee")
            continue

        old_link = shopee_links[0]

        if idx < len(converted_links) and converted_links[idx]:
            new_link = converted_links[idx]
            updated_content = content.replace(old_link, new_link)
            f.write_text(updated_content, encoding='utf-8')
            print(f"✅ {f.parent.name}/{f.name}: อัปเดตสำเร็จ")
            print(f"   เก่า: {old_link[:60]}...")
            print(f"   ใหม่: {new_link[:60]}...")
            updated_count += 1
        else:
            print(f"⚠️  {f.parent.name}/{f.name}: ไม่มีลิงก์ที่แปลงแล้ว (index {idx})")

    if updated_count == 0:
        print(f"\n❌ ไม่มีไฟล์ที่อัปเดต")
        return False

    print(f"\n✅ อัปเดต {updated_count} ไฟล์ด้วย affiliate links เรียบร้อย!")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Update posts with converted affiliate links")
    parser.add_argument("date", nargs="?", help="Date folder (YYYY-MM-DD), default: today")
    parser.add_argument("--input", "-i", default="_converted_links.txt",
                        help="Input file with converted links")
    parser.add_argument("--dir", help="Override directory path")
    args = parser.parse_args()

    success = update_captions(args.date, args.input, args.dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
