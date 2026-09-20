from pathlib import Path
import os, re
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

key = os.getenv("KIPRIS_API_KEY")
raw_dir = ROOT / "data" / "raw" / "kipris"

print("=" * 78)
print("KIPRIS PRECHECK")
print("=" * 78)
print("API KEY        :", "SET" if key and key.strip() else "NOT SET")
print("RAW DIR        :", raw_dir)
print("RAW DIR EXISTS :", raw_dir.exists())

files = [p for p in raw_dir.rglob("*") if p.is_file() and p.name != ".gitkeep"] if raw_dir.exists() else []
print("RAW FILES      :", len(files))
for p in files[:20]:
    print(" -", p.relative_to(ROOT))

print()
print("NEXT:")
if not key or not key.strip():
    print("KIPRIS_API_KEY is NOT SET.")
    print("공식 KIPRISPlus API 샘플 호출은 아직 실행하지 않습니다.")
    print("키를 임의 생성하거나 웹검색 결과를 특허 원자료처럼 저장하지 않습니다.")
else:
    print("KIPRIS_API_KEY is SET.")
    print("다음 단계에서 ABS/ESC/통합제동/BBW·EMB 소량 샘플 호출을 진행할 수 있습니다.")
print("=" * 78)
