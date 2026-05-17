// ==============================================================
//  OpenClaw Shopee Scraper — Console Snippet
//  วิธีใช้:
//    1. ไปหน้า Shopee search (shopee.co.th/search?keyword=xxx)
//    2. Scroll ลงให้เห็นสินค้าที่ต้องการ
//    3. กด F12 → Console tab
//    4. Copy ทั้งหมดนี้ วางใน Console → Enter
//    5. ไฟล์ CSV จะดาวน์โหลดอัตโนมัติ
// ==============================================================

(() => {
  // ดึง product links ทั้งหมด
  const links = document.querySelectorAll('a[href*="-i."]');
  const seen = new Set();
  const products = [];

  for (const a of links) {
    const href = a.getAttribute("href") || "";
    if (!href.match(/-i\.\d+\.\d+/)) continue;

    const fullUrl = href.startsWith("http")
      ? href
      : "https://shopee.co.th" + href;
    if (seen.has(fullUrl)) continue;
    seen.add(fullUrl);

    // หา product card container
    let card = a;
    for (let i = 0; i < 8; i++) {
      if (!card.parentElement) break;
      card = card.parentElement;
      if (card.tagName === "LI" || card.getAttribute("data-sqe")) break;
    }

    const text = card.innerText || "";
    const lines = text
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => l.length > 0);

    // ชื่อสินค้า: บรรทัดแรกที่ไม่ใช่ราคา/ส่วนลด
    let name = "";
    for (const line of lines) {
      if (
        line.length > 5 &&
        !line.match(/^฿/) &&
        !line.match(/^\d+%/) &&
        !line.includes("ขายแล้ว") &&
        !line.match(/^\d+$/) &&
        !line.includes("จัดส่งฟรี") &&
        !line.includes("ถูกใจ") &&
        !line.includes("โฆษณา") &&
        !line.includes("Ad")
      ) {
        name = line;
        break;
      }
    }

    // ราคา
    let price = "0";
    const pm = text.match(/฿([\d,]+(?:\.\d+)?)/);
    if (pm) price = pm[1].replace(/,/g, "");

    // รูปภาพ
    let imageUrl = "";
    const img = card.querySelector(
      'img[src*="susercontent"], img[src*="down-"]'
    );
    if (img) imageUrl = img.src || "";

    if (name && name.length > 3) {
      products.push({ name: name.substring(0, 200), price, url: fullUrl, image_url: imageUrl });
    }
  }

  if (products.length === 0) {
    console.log("❌ ไม่พบสินค้า — ลอง scroll ลงก่อนแล้วรันใหม่");
    alert("❌ ไม่พบสินค้า — ลอง scroll ลงให้เห็นสินค้าก่อนแล้วรันอีกครั้ง");
    return;
  }

  // สร้าง CSV
  const BOM = "\uFEFF";
  const header = "name,price,url,image_url\n";
  const rows = products
    .map((p) => {
      const n = '"' + p.name.replace(/"/g, '""') + '"';
      return `${n},${p.price},${p.url},${p.image_url}`;
    })
    .join("\n");

  const csv = BOM + header + rows;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a2 = document.createElement("a");
  a2.href = url;
  a2.download = `shopee_${new Date().toISOString().slice(0, 10)}.csv`;
  a2.click();
  URL.revokeObjectURL(url);

  // สรุป
  console.log(`✅ ดึงได้ ${products.length} สินค้า → ดาวน์โหลด CSV แล้ว!`);
  console.table(products.slice(0, 10));

  // ส่งไป Dashboard (ถ้าเปิดอยู่)
  fetch("http://localhost:5000/api/shopee/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ products, keyword: new URLSearchParams(window.location.search).get("keyword") || "unknown" }),
  })
    .then((r) => r.json())
    .then((d) => console.log("📡 ส่ง Dashboard:", d))
    .catch(() => console.log("ℹ️ Dashboard ไม่ได้เปิด — ใช้ CSV ที่ดาวน์โหลดแทน"));
})();
