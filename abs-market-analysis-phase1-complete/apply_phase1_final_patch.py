from pathlib import Path
import shutil, re

app = Path("dashboard/app.py")
if not app.exists():
    raise SystemExit("ERROR: dashboard/app.py를 찾지 못했습니다. 프로젝트 루트에서 실행하세요.")

backup = Path("dashboard/app_before_phase1_final.py")
if not backup.exists():
    shutil.copy2(app, backup)

s = app.read_text(encoding="utf-8-sig")

# 1. Global rule: do not turn missing observations into zero.
# Only remove obvious display/data fillna(0) patterns. Text/boolean fills are untouched.
patterns = [
    (r'(\[\s*["\']value["\']\s*\]\s*)\.fillna\(\s*0(?:\.0)?\s*\)', r'\1'),
    (r'pd\.to_numeric\(([^,\n]+),\s*errors=["\']coerce["\']\)\.fillna\(\s*0(?:\.0)?\s*\)', r'pd.to_numeric(\1, errors="coerce")'),
]
for pat, rep in patterns:
    s = re.sub(pat, rep, s)

# 2. User-facing wording fixed for the final version.
s = s.replace("기회", "다음 확인(Action)")
s = s.replace("내수 시장 구조", "제동기술 전환 방향")
s = s.replace("12개월 표준편차", "변화율 기반 12개월 변동성(%)")

# 3. Correct arrows when the code uses a fixed upward arrow before a YoY expression.
s = re.sub(r'↑\s*(\{[^{}]*yoy[^{}]*\})', r'\1', s, flags=re.I)

# 4. Add the final analysis principles in the footer if not already present.
rule = "NULL/미수집 월은 0으로 대체하지 않음 · 실제 관측값만 사용 · 관찰(Fact)과 해석(Why)을 구분"
if rule not in s:
    s += f'\n\n# PHASE1 FINAL RULE\n# {rule}\n'

app.write_text(s, encoding="utf-8-sig")
print("PHASE1 FINAL PATCH COMPLETE")
print("BACKUP :", backup)
print("UPDATED:", app)
print("RULE   :", rule)
