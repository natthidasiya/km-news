# KM Next+ — อัปเดตเองทุกจันทร์ 07:00
โครงสร้าง
- fetch.py     Claude ค้นเว็บ อ่านข่าวจริง แปล+สรุปไทย ใส่ #แท็ก → สะสมใน data/archive.json → สร้าง docs/index.html
- data/archive.json  คลังความรู้ทั้งหมด (ใช้แทน database — เก็บใน repo, มีประวัติทุกสัปดาห์)
- template.html หน้าตาเว็บ (โลโก้+ภาพพื้นหลังฝังในไฟล์แล้ว)
- .github/workflows/weekly.yml  ตัวตั้งเวลา
- supabase.sql (ไม่บังคับ) นับยอดถูกใจรวมทุกคน

ติดตั้ง
1. GitHub → New repository (Public) → Upload files ทั้งหมดในโฟลเดอร์นี้ (รวม .github)
2. Settings > Secrets and variables > Actions → New secret `ANTHROPIC_API_KEY`
3. Settings > Pages → Deploy from branch → main / docs
4. Actions → KM News Weekly → Run workflow (รอบแรก)
5. ลิงก์ https://<user>.github.io/<repo>/ → แปะใน SharePoint ครั้งเดียว

แก้คำค้น/จำนวนเรื่อง: แก้ PILLARS ใน fetch.py
ลบเรื่องที่ไม่ต้องการ: ลบรายการใน data/archive.json แล้วกด Run workflow


ยอดถูกใจรวมทุกคน (ไม่บังคับ): supabase.com → New project → SQL Editor → รัน supabase.sql → ใส่ secret SUPABASE_URL, SUPABASE_ANON_KEY → Run workflow
