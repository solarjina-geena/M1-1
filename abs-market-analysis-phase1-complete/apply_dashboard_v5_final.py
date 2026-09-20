from pathlib import Path
import shutil, datetime

root=Path.cwd()
src=root/"dashboard_app_v5_final.py"
dst=root/"dashboard"/"app.py"
if not src.exists():
    raise SystemExit("ERROR: dashboard_app_v5_final.py가 현재 폴더에 없습니다.")
if not dst.exists():
    raise SystemExit("ERROR: dashboard/app.py를 찾지 못했습니다. 프로젝트 루트에서 실행하세요.")

stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup=root/"dashboard"/f"app_before_v5_final_{stamp}.py"
shutil.copy2(dst,backup)
shutil.copy2(src,dst)

print("ABS DASHBOARD V5 FINAL PATCH COMPLETE")
print("BACKUP :", backup)
print("UPDATED:", dst)
print("RUN    : python -m streamlit run .\\dashboard\\app.py")
