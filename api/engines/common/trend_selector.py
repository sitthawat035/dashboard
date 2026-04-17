"""
Smart Trend Selector
====================
แก้ปัญหา: Score-based system เลือก trend เดิมซ้ำทุกวัน

Features:
  - History tracking (trend_history.json)
  - Velocity bonus: ของใหม่ได้ bonus, ของเก่า penalized
  - Recency penalty: topic ที่เลือกไปแล้ว N วัน ถูก penalized หรือ blacklist
  - Similarity filter: ตัด topic ที่คล้ายกับของที่เลือกไปแล้วออก (fuzzy match)
  - Diversity enforcement: เลือกได้ไม่เกิน 1 topic ต่อ category เดียวกัน
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path


# ─── Configurable Settings ───────────────────────────────────────────────────
BLACKLIST_DAYS = 7          # topic ที่เลือกไปแล้วจะถูก blacklist กี่วัน
SIMILARITY_THRESHOLD = 0.55  # ค่า overlap ratio ที่ถือว่า "คล้ายกัน" (0.0-1.0)
VELOCITY_BONUS_NEW = 3.0    # bonus สำหรับ topic ที่ไม่เคยเห็นมาก่อน
VELOCITY_BONUS_SEEN_ONCE = 1.0  # bonus สำหรับเห็นมาแล้ว 1 ครั้ง
RECENCY_PENALTY_3D = 5.0   # penalty ถ้าเลือกไปน้อยกว่า 3 วัน
RECENCY_PENALTY_7D = 2.0   # penalty ถ้าเลือกไปน้อยกว่า 7 วัน


# ─── Categories (ใช้ Diversity Enforcement) ──────────────────────────────────
TECH_CATEGORIES = {
    "ai": ["ai", "artificial intelligence", "machine learning", "llm", "gpt", "chatgpt", "gemini", "claude"],
    "ev_robot": ["robot", "humanoid", "tesla", "ev", "electric", "autonomous"],
    "crypto": ["crypto", "bitcoin", "ethereum", "blockchain", "defi", "web3"],
    "startup": ["startup", "funding", "ipo", "venture", "series a", "unicorn"],
    "biotech": ["health", "biotech", "medical", "drug", "gene", "สุขภาพ"],
    "space": ["space", "nasa", "spacex", "satellite", "rocket"],
    "other": [],  # catch-all
}

SHOPEE_CATEGORIES = {
    "skincare": ["สกินแคร์", "ครีม", "เซรั่ม", "กันแดด", "มอยเจอร์", "skin", "toner", "cleanser"],
    "gadget": ["gadget", "แกดเจ็ต", "อุปกรณ์", "ขาจับ", "earphone", "หูฟัง", "สาย"],
    "lifestyle": ["ของตกแต่ง", "บ้าน", "lifestyle", "กระเป๋า", "ชุด"],
    "food_health": ["อาหาร", "วิตามิน", "supplement", "collagen", "สมุนไพร"],
    "fashion": ["เสื้อผ้า", "รองเท้า", "แฟชั่น", "ชุดออกกำลัง", "กีฬา"],
    "other": [],
}


def _normalize(text: str) -> str:
    return re.sub(r"[^\w\u0E00-\u0E7F\s]", "", text.lower()).strip()


def _word_overlap(a: str, b: str) -> float:
    """Simple word overlap ratio (Jaccard-like)"""
    words_a = set(_normalize(a).split())
    words_b = set(_normalize(b).split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def _detect_category(text: str, category_map: dict) -> str:
    """Detect which category a topic/keyword belongs to"""
    normalized = _normalize(text)
    for cat, keywords in category_map.items():
        if cat == "other":
            continue
        for kw in keywords:
            if kw in normalized:
                return cat
    return "other"


class TrendSelector:
    """
    Smart Trend Selector with memory, velocity scoring, and diversity enforcement.
    
    Usage:
        selector = TrendSelector()
        
        # Score and filter AI's raw candidates
        best_topics = selector.filter_and_rank(
            candidates=[{"topic": "DeepSeek AI", "reason": "..."}, ...],
            kind="lookforward",   # or "shopee"
            top_n=3
        )
        
        # After selection, mark them (updates history + blacklist)
        selector.mark_selected(best_topics, kind="lookforward")
    """

    def __init__(self, history_path: str = None):
        if history_path is None:
            history_path = Path(__file__).resolve().parent.parent / "trend_history.json"
        self.history_path = Path(history_path)
        self.history = self._load()

    # ─── Public API ──────────────────────────────────────────────────────────

    def filter_and_rank(self, candidates: list, kind: str = "lookforward", top_n: int = 3) -> list:
        """
        Filter and rank raw AI candidates.
        
        candidates: list of dicts
          - lookforward: [{"topic": "...", "reason": "..."}]
          - shopee:      [{"keyword": "...", "trend_score": N}]
        kind: "lookforward" or "shopee"
        top_n: max items to return
        """
        category_map = TECH_CATEGORIES if kind == "lookforward" else SHOPEE_CATEGORIES
        text_key = "topic" if kind == "lookforward" else "keyword"

        scored = []
        for item in candidates:
            text = item.get(text_key, "")
            base_score = float(item.get("trend_score", 7))  # lookforward items default 7
            final = self._compute_score(text, base_score, kind)
            scored.append({**item, "_score": final, "_category": _detect_category(text, category_map)})

        # Sort descending
        scored.sort(key=lambda x: x["_score"], reverse=True)

        # Diversity: max 1 per category (unless category = "other")
        selected = []
        used_categories = set()
        for item in scored:
            cat = item["_category"]
            if cat != "other" and cat in used_categories:
                continue
            # Similarity check vs already selected
            if self._too_similar_to_selected(item[text_key], selected, text_key):
                continue
            selected.append(item)
            if cat != "other":
                used_categories.add(cat)
            if len(selected) >= top_n:
                break

        # If still not enough (all filtered), fill from remainder without diversity check
        if len(selected) < top_n:
            for item in scored:
                if item not in selected:
                    selected.append(item)
                if len(selected) >= top_n:
                    break

        # Clean internal keys before returning
        return [{k: v for k, v in item.items() if not k.startswith("_")} for item in selected]

    def mark_selected(self, items: list, kind: str = "lookforward"):
        """Record selected topics/keywords in history and apply blacklist."""
        today = datetime.now().strftime("%Y-%m-%d")
        text_key = "topic" if kind == "lookforward" else "keyword"
        
        texts = [item.get(text_key, "") for item in items if item.get(text_key)]

        # Add to history
        entry = {
            "date": today,
            "kind": kind,
            "items": texts,
        }
        self.history.setdefault("selections", []).append(entry)

        # Add to blacklist
        blacklist_until = (datetime.now() + timedelta(days=BLACKLIST_DAYS)).strftime("%Y-%m-%d")
        for text in texts:
            key = _normalize(text)
            self.history.setdefault("blacklist", {})[key] = blacklist_until

        self._save()

    def get_history_summary(self) -> str:
        """Returns a human-readable summary of recent selections (for AI prompt injection)."""
        selections = self.history.get("selections", [])
        recent = [s for s in selections if self._days_since(s["date"]) <= 14]
        if not recent:
            return "(ยังไม่มีประวัติ)"
        
        lines = []
        for s in sorted(recent, key=lambda x: x["date"], reverse=True)[:10]:
            items_str = ", ".join(s["items"])
            lines.append(f"  [{s['date']}] {s['kind']}: {items_str}")
        return "\n".join(lines)

    # ─── Internal Scoring ─────────────────────────────────────────────────────

    def _compute_score(self, text: str, base_score: float, kind: str) -> float:
        key = _normalize(text)
        score = base_score

        # Check blacklist
        if self._is_blacklisted(key):
            return -999.0

        # Velocity bonus
        times_seen = self._times_seen(text, kind)
        if times_seen == 0:
            score += VELOCITY_BONUS_NEW
        elif times_seen == 1:
            score += VELOCITY_BONUS_SEEN_ONCE

        # Recency penalty
        days_since_last = self._days_since_last_selection(text, kind)
        if days_since_last is not None:
            if days_since_last < 3:
                score -= RECENCY_PENALTY_3D
            elif days_since_last < 7:
                score -= RECENCY_PENALTY_7D

        return round(score, 2)

    def _is_blacklisted(self, normalized_key: str) -> bool:
        blacklist = self.history.get("blacklist", {})
        if normalized_key not in blacklist:
            return False
        until = datetime.strptime(blacklist[normalized_key], "%Y-%m-%d")
        return datetime.now() < until

    def _times_seen(self, text: str, kind: str) -> int:
        count = 0
        for sel in self.history.get("selections", []):
            if sel.get("kind") != kind:
                continue
            for item in sel.get("items", []):
                if _word_overlap(text, item) >= SIMILARITY_THRESHOLD:
                    count += 1
        return count

    def _days_since_last_selection(self, text: str, kind: str) -> float | None:
        latest = None
        for sel in self.history.get("selections", []):
            if sel.get("kind") != kind:
                continue
            for item in sel.get("items", []):
                if _word_overlap(text, item) >= SIMILARITY_THRESHOLD:
                    days = self._days_since(sel["date"])
                    if latest is None or days < latest:
                        latest = days
        return latest

    def _too_similar_to_selected(self, text: str, already_selected: list, text_key: str) -> bool:
        for item in already_selected:
            if _word_overlap(text, item.get(text_key, "")) >= SIMILARITY_THRESHOLD:
                return True
        return False

    def _days_since(self, date_str: str) -> float:
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            return (datetime.now() - d).total_seconds() / 86400
        except Exception:
            return 999.0

    # ─── Persistence ─────────────────────────────────────────────────────────

    def _load(self) -> dict:
        if self.history_path.exists():
            try:
                return json.loads(self.history_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"selections": [], "blacklist": {}}

    def _save(self):
        # Prune blacklist entries that have expired
        today = datetime.now().strftime("%Y-%m-%d")
        self.history["blacklist"] = {
            k: v for k, v in self.history.get("blacklist", {}).items() if v >= today
        }
        # Keep only last 90 days of selections
        cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        self.history["selections"] = [
            s for s in self.history.get("selections", []) if s.get("date", "") >= cutoff
        ]
        self.history_path.write_text(
            json.dumps(self.history, ensure_ascii=False, indent=2), encoding="utf-8"
        )
