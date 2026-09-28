"""KM News Digest: Claude (web search) หา+อ่าน+สรุป -> สะสมลง data/archive.json -> สร้าง docs/index.html"""
import json, os, re, datetime as dt
from pathlib import Path
import anthropic

TZ = dt.timezone(dt.timedelta(hours=7))
ARCH = Path("data/archive.json")
TAGS = "#AI-at-Work #Prompting #Automation #Meeting #Writing #Focus #Learning #Collaboration #Decision #DataSkills #Wellbeing #Leadership #KM-Strategy #Lessons-Learned #CoP #Benchmark #KnowledgeGraph #RAG #AI-Agent #Digital-Expert"
PILLARS = {
  "WORLD": ("องค์กรอื่นทำ KM อย่างไร benchmark เทรนด์โลก KM award case study", 14, 6,
            ['"knowledge management" case study', '"lessons learned" program organization', 'knowledge management award company', 'APQC KMWorld']),
  "FUTURE": ("AI Agent, Knowledge Graph, RAG, AI-powered learning, Digital Expert ที่เปลี่ยนงานความรู้", 14, 6,
             ['"AI agent" knowledge work enterprise', 'GraphRAG knowledge graph enterprise', 'RAG knowledge base', 'AI corporate learning']),
  "HACK": ("เทคนิคทำงานที่นำไปใช้ได้ทันทีในยุค AI จากแหล่งน่าเชื่อถือทั่วโลก เช่น HBR MIT Sloan Fast Company Atlassian Microsoft WorkLab Zapier", 30, 5,
           ['work smarter AI tips', 'productivity technique research', 'better meetings tips', 'prompt tips for work', 'deep work focus method']),
}
RULES = """ตอบเป็น JSON array เท่านั้น ห้ามมีข้อความอื่นหรือ markdown:
[{"title_th":"หัวข้อไทยชัดเจน ไม่แปลตรงตัว",
  "summary_th":"แปลและสรุปเนื้อข่าวเป็นภาษาไทยด้วยคำของตัวเอง 5-7 ประโยค (~120-180 คำ): เกิดอะไร/แนวคิดคืออะไร ทำงานอย่างไร ตัวเลขหรือตัวอย่างสำคัญ ทำไมสำคัญ ห้าม bullet ห้ามคัดลอกยาวเกิน 15 คำ",
  "so_what":"%s 1 ประโยค",
  "tags":["1-3 แท็กจากรายการ: %s"],
  "score":6-10,"link":"URL บทความต้นฉบับ","src":"ชื่อสำนักข่าว","date":"YYYY-MM-DD"}]
ต้องเปิดอ่านบทความจริงก่อนสรุป ตัดโฆษณาขายของ ตัดข่าวนอกช่วงเวลา ไม่มีข่าวดีพอให้ส่งน้อยลง ห้ามแต่งข่าว"""

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

def main():
    arch = json.loads(ARCH.read_text(encoding="utf-8")) if ARCH.exists() else []
    seen = [a["link"] for a in arch]
    week = dt.datetime.now(TZ).strftime("%Y-%m-%d")
    new = []
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
