# 🦞 SHOPEE AFFILIATE - THE ULTIMATE SIMPLE WAY

## ⚡ One Command to Rule Them All

```bash
python tools/shopee.py
```

**That's it.** No parameters. No thinking. Just run it.

---

## 🎯 What Happens

Automatically runs:
1. ✨ **Generate Content** → captions + download images
2. 🌐 **Extract Links** → from captions
3. 🔗 **Convert to Affiliate** → short links (requires Chrome login)
4. 📝 **Update Captions** → with affiliate links

---

## 🚀 How to Use

### Method 1: Command Line (Easiest)
```bash
cd shopee_affiliate
python tools/shopee.py
```

### Method 2: Double-Click (Windows)
1. Go to `shopee_affiliate/`
2. Double-click `shopee.bat`
3. Done!

### Method 3: PowerShell
```powershell
cd shopee_affiliate
python tools/shopee.py
```

---

## ⚠️ One Manual Step

When script asks: **"Press ENTER when you're logged in to Affiliate..."**

1. Chrome will open automatically
2. Go to: https://affiliate.shopee.co.th
3. LOGIN with your Shopee account
4. Keep Chrome open
5. Press ENTER in the command window

That's the only manual step needed!

---

## 📂 Output

All files saved to: `data/05_ReadyToPost/YYYY-MM-DD/`

```
data/05_ReadyToPost/2026-02-21/
├── 08.00/
│   ├── caption.txt ✓ (with affiliate link)
│   └── product_image.webp
├── 12.00/
│   ├── caption.txt ✓ (with affiliate link)
│   └── product_image.webp
├── 18.00/
│   ├── caption.txt ✓ (with affiliate link)
│   └── product_image.webp
└── 22.00/
    ├── caption.txt ✓ (with affiliate link)
    └── product_image.webp
```

---

## 🎓 Behind The Scenes

This script automatically:
- Loads products from CSV
- Uses AI to select 4 best products
- Writes captions in "เพื่อนสายป้ายยา" style
- Downloads product images
- Extracts Shopee links
- Opens Chrome for link conversion
- Converts to affiliate short links
- Updates captions with converted links

All handled automatically. You just press ENTER once.

---

## 🆘 Troubleshooting

### Chrome won't open?
- Make sure Chrome is installed
- Run manually: `chrome.exe --remote-debugging-port=9222`
- Then continue the script

### "Not logged in" error?
- Make sure you visited https://affiliate.shopee.co.th
- Logged in with your account
- Kept Chrome window open

### Links not converting?
- Check Chrome port 9222 is still open
- You're logged in to Affiliate
- Try again

---

## 💡 Tips

- Run this **once per day** to generate 4 posts
- Adjust products in CSV before running
- Content is saved immediately (safe to stop anytime)

---

**Version:** 2.0 Ultimate Simple  
**Status:** Production Ready ✅  
**Time to run:** ~5 minutes

🚀 Happy posting!
