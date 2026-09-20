import requests
from pathlib import Path

urls = [
    (
        "PDF",
        "https://www.motir.go.kr/attach/down/095a2dda9c864e1d90d751f7668a1117/4510eca3d1b6417a8841740dd3315014/9a9db098b587ee18b321c826f3707a49"
    ),
    (
        "HWPX",
        "https://www.motir.go.kr/attach/down/095a2dda9c864e1d90d751f7668a1117/4510eca3d1b6417a8841740dd3315014/778bdbf5db9ced7c8fd52756c00bf0cd"
    ),
    (
        "HWP",
        "https://www.motir.go.kr/attach/down/095a2dda9c864e1d90d751f7668a1117/4510eca3d1b6417a8841740dd3315014/13055e35ba7465cb478c5b4be490c5a8"
    ),
]

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.motir.go.kr/kor/article/ATCL3f49a5a8c/167094/view",
}

outdir = Path("data/raw/motie/monthly_pdf/recovered_pdf")
outdir.mkdir(parents=True, exist_ok=True)

for kind, url in urls:
    print("=" * 80)
    print(kind)

    try:
        r = requests.get(
            url,
            headers=headers,
            timeout=30,
            allow_redirects=True
        )

        print("STATUS       :", r.status_code)
        print("FINAL URL    :", r.url)
        print("CONTENT-TYPE :", r.headers.get("Content-Type"))
        print("BYTES        :", len(r.content))
        print("FIRST BYTES  :", r.content[:20])

        if r.status_code == 200 and len(r.content) > 10000:
            ext = {
                "PDF": ".pdf",
                "HWPX": ".hwpx",
                "HWP": ".hwp"
            }[kind]

            out = outdir / ("2023-03" + ext)
            out.write_bytes(r.content)

            print("SAVED        :", out)
        else:
            print("NOT SAVED")

    except Exception as e:
        print("ERROR        :", repr(e))
