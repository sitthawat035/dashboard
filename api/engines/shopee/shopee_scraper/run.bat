@echo off
chcp 65001 >nul
echo.
echo  === Shopee Scraper ===
echo.
echo  ครั้งแรก Browser จะเปิดให้ login Shopee ด้วยตนเอง
echo  หลัง login ครั้งเดียว cookies จะถูกบันทึกอัตโนมัติ
echo.
echo  ตัวอย่าง:
echo    python shopee_scraper.py --keyword "เสื้อยืด" --limit 50
echo    python shopee_scraper.py --keyword "iPhone" --sort sales
echo.
python "%~dp0shopee_scraper.py" %*
pause
