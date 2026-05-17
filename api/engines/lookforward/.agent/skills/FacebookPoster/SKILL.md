---
name: FacebookPoster
description: Automate posting content to Facebook Page using browser automation (Playwright/Chrome CDP).
---

# FacebookPoster Skill

This skill automates the process of posting text and media to a Facebook Page using a real Chrome browser session.

## 🚀 Capabilities

1.  **Post Text & Hashtags**: Posts content from markdown drafts.
2.  **Upload Media**: Attaches photos/videos to the post.
3.  **Human-like Behavior**: Uses realistic delays and typing speeds.
4.  **No API Needed**: Uses existing browser session (cookies).

## 📋 Steps

1.  **Connect to Browser**: Connects to running Chrome (port 9222).
2.  **Navigate**: Goes to Facebook Home or Business Suite.
3.  **Create Post**: Finds and clicks "What's on your mind?" or "Create Post".
4.  **Input Content**:
    *   Types/Pastes text caption.
    *   Uploads attached media files.
5.  **Post**: Clicks the "Post" button.
6.  **Verify**: Checks for success confirmation.

## 🛠️ Usage

```bash
# Post text only
python .agent/skills/FacebookPoster/poster.py --file "04_Drafts/approved/my_post.md"

# Post with media
python .agent/skills/FacebookPoster/poster.py --file "04_Drafts/approved/my_post.md" --media "03_Media/image1.jpg"
```

## ⚠️ Requirements

*   Chrome must be running with remote debugging:
    `chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\ChromeProfile"`
*   User must be logged into Facebook.
