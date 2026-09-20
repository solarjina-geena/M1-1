from pathlib import Path
import shutil, py_compile

ROOT=Path(__file__).resolve().parent
SRC=ROOT/"dashboard_app_v4.py"
TARGET=ROOT/"dashboard"/"app.py"
BACKUP=ROOT/"dashboard"/"app_before_v4.py"

if not SRC.exists():
    raise FileNotFoundError(f"패치 파일 없음: {SRC}")
if not TARGET.parent.exists():
    raise FileNotFoundError(f"dashboard 폴더 없음: {TARGET.parent}")

if TARGET.exists():
    shutil.copy2(TARGET,BACKUP)
shutil.copy2(SRC,TARGET)
py_compile.compile(str(TARGET),doraise=True)

print("ABS DASHBOARD V4 PATCH COMPLETE")
print("BACKUP :", BACKUP.relative_to(ROOT))
print("UPDATED:", TARGET.relative_to(ROOT))
print("RUN    : streamlit run app.py")
