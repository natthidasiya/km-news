"""KM News Digest: Claude (web search) หา+อ่าน+สรุป -> สะสมลง data/archive.json -> สร้าง docs/index.html"""
import json, os, re, datetime as dt
from pathlib import Path
import anthropic
import urllib.request, urllib.parse, html as _html

def og_image(url):
    """ดึงภาพปก (og:image) จากลิงก์ต้นฉบับ ไว้แสดงเป็นภาพประกอบพร้อมลิงก์กลับ"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (KM-News-Digest)"})
        raw = urllib.request.urlopen(req, timeout=10).read(400_000).decode("utf-8", "ignore")
        for pat in (r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]*content=["\']([^"\']+)',
                    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*property=["\']og:image',
                    r'<meta[^>]+name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)'):
            m = re.search(pat, raw, re.I)
            if m:
                return urllib.parse.urljoin(url, _html.unescape(m.group(1).strip()))
    except Exception as e:
        print("no image", url[:60], e)
    return ""

def fill_images(arch, limit=40):
    n = 0
    for it in arch:
        if "image" not in it and n < limit:
            it["image"] = og_image(it["link"]); n += 1


TZ = dt.timezone(dt.timedelta(hours=7))
ARCH = Path("data/archive.json")
TAGS = "#AI-at-Work #Prompting #Automation #Meeting #Writing #Focus #Learning #Collaboration #Decision #DataSkills #Wellbeing #Leadership #KM-Strategy #Lessons-Learned #CoP #Benchmark #KnowledgeGraph #RAG #AI-Agent #Digital-Expert"
PILLARS = {
  "WORLD": ("องค์กรอื่นทำ KM อย่างไร benchmark เทรนด์โลก KM award case study", 14, 6,
            ['"knowledge management" case study', '"lessons learned" program organization', 'knowledge management award company', 'APQC KMWorld']),
  "FUTURE": ("AI Agent, Knowledge Graph, RAG, AI-powered learning, Digital Expert ที่เปลี่ยนงานความรู้", 14, 6,
             ['"AI agent" knowledge work enterprise', 'GraphRAG knowledge graph enterprise', 'RAG knowledge base', 'AI corporate learning']),
  "HACK": ("เทคนิคทำงานที่นำไปใช้ได้ทันที ไม่จำกัดแค่ AI: ประชุม การเขียน/สื่อสาร สมาธิ/เวลา การตัดสินใจ การทำงานเป็นทีม/feedback การเรียนรู้ wellbeing นิสัยผู้นำ และ AI กับงาน โดย AI ไม่เกิน 2 ใน 5 เรื่อง แหล่งน่าเชื่อถือ เช่น HBR MIT Sloan Fast Company Atlassian Microsoft WorkLab", 30, 5,
           ['better meetings research', 'clear business writing technique', 'deep work focus method', 'decision making framework', 'feedback technique manager', 'burnout prevention habit']),
}
RULES = """ตอบเป็น JSON array เท่านั้น ห้ามมีข้อความอื่นหรือ markdown:
[{"title_th":"หัวข้อไทยชัดเจน ไม่แปลตรงตัว ถ้ามีตัวเลขเด่นให้ใส่ในหัวข้อ",
  "summary_th":"แปลและสรุปเนื้อข่าวเป็นภาษาไทยด้วยคำของตัวเอง 5-7 ประโยค (~120-180 คำ): เกิดอะไร/แนวคิดคืออะไร ทำงานอย่างไร ตัวเลขหรือตัวอย่างสำคัญ ทำไมสำคัญ ห้าม bullet ห้ามคัดลอกยาวเกิน 15 คำ",
  "takeaways":["Key takeaway 3-5 ข้อ ข้อละ 1 ประโยคสั้น ไม่ลงรายละเอียด (ทุกหมวด)"],
  "stat":{"value":"ตัวเลขเด่นที่สุดจากบทความ เช่น 54%% หรือ 3","label":"คำอธิบายไทยสั้นไม่เกิน 8 คำ"},
  "so_what":"%s 1 ประโยค",
  "tags":["1-3 แท็กจากรายการ: %s"],
  "score":6-10,"link":"URL บทความต้นฉบับ","src":"ชื่อสำนักข่าว","date":"YYYY-MM-DD"}]
ค้นแหล่งไทยด้วย 1-2 query (เช่น สถาบันเพิ่มผลผลิตแห่งชาติ TMA SEAC Techsauce The Standard Brand Inside) ใส่เรื่องไทยเฉพาะที่น่าสนใจจริง มีกรณีศึกษา ข้อมูล หรือวิธีที่มีสาระ ถ้าไม่มีไม่ต้องใส่ ห้าม PR/ข่าวอีเวนต์/บทความแปลซ้ำ
ต้องเปิดอ่านบทความจริงก่อนสรุป ตัดโฆษณาขายของ ตัดข่าวนอกช่วงเวลา ไม่มีข่าวดีพอให้ส่งน้อยลง ห้ามแต่งข่าว ถ้าบทความไม่มีตัวเลขเด่นให้ตัด stat ออก ห้ามแต่งตัวเลข"""

def ask(pillar, seen):
    desc, days, n, qs = PILLARS[pillar]
    sw = "ลองทำ: ก้าวแรกที่ลองได้ทันที" if pillar == "HACK" else "ต่อยอด: CPF KM เอาไปต่อยอดอย่างไร"
    prompt = (f"คุณคือ KM Curator ของ CPF (อาหาร FMCG ไทย) หาเนื้อหาหมวด: {desc}\n"
              f"ช่วงเวลา: {days} วันล่าสุด ถึง {dt.date.today()} ค้นด้วย query เหล่านี้เป็นแนวทาง: {qs}\n"
              f"เลือกดีที่สุด {n} เรื่อง ห้ามซ้ำกับลิงก์ที่มีแล้ว: {seen[-80:]}\n" + RULES % (sw, TAGS))
    r = anthropic.Anthropic().messages.create(
        model="claude-sonnet-5", max_tokens=12000,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 10}],
        messages=[{"role": "user", "content": prompt}])
    txt = [b.text for b in r.content if b.type == "text"][-1]
    txt = re.sub(r"```json|```", "", txt).strip()
    txt = txt[txt.find("["): txt.rfind("]") + 1]
    return json.loads(txt)

def add(arch, items, week):
    seen = {a["link"] for a in arch}; new = []
    for it in items:
        if not it.get("link") or it["link"] in seen: continue
        seen.add(it["link"])
        new.append({**it, "week": week, "uid": re.sub(r"\W+", "", it["link"])[-48:]})
    return new

def main():
    arch = json.loads(ARCH.read_text(encoding="utf-8")) if ARCH.exists() else []
    seen = [a["link"] for a in arch]
    week = dt.datetime.now(TZ).strftime("%Y-%m-%d")
    new = []
    # โหมดฟรี: ไม่มี API key -> รับข่าวจาก data/new.json (ผลจากสกิล km-news-scout)
    NEW = Path("data/new.json")
    if not os.getenv("ANTHROPIC_API_KEY"):
        if NEW.exists():
            new = add(arch, json.loads(NEW.read_text(encoding="utf-8")), week)
            NEW.unlink()
        arch = new + arch
        fill_images(arch)
        ARCH.write_text(json.dumps(arch, ensure_ascii=False, indent=1), encoding="utf-8")
        build(arch); print(f"free mode: added {len(new)} / total {len(arch)}"); return
    for p in PILLARS:
        try:
            for it in ask(p, seen):
                if it.get("link") in seen: continue
                seen.append(it["link"])
                new.append({**it, "pillar": p, "week": week,
                            "uid": re.sub(r"\W+", "", it["link"])[-48:]})
        except Exception as e:
            print("skip", p, e)
    arch = new + arch
    fill_images(arch)
    ARCH.parent.mkdir(exist_ok=True)
    ARCH.write_text(json.dumps(arch, ensure_ascii=False, indent=1), encoding="utf-8")
    build(arch)
    print(f"added {len(new)} / total {len(arch)}")

def build(arch):
    data = {"updated": dt.datetime.now(TZ).strftime("%d/%m/%Y %H:%M"), "items": arch}
    html = Path("template.html").read_text(encoding="utf-8").replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False))
    for k in ("SUPABASE_URL", "SUPABASE_ANON_KEY"):
        html = html.replace(f"__{k}__", os.getenv(k, ""))
    Path("docs").mkdir(exist_ok=True)
    Path("docs/index.html").write_text(html, encoding="utf-8")

if __name__ == "__main__":
    main()
