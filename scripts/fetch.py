"""各ソースから介護事業所・医療機関データを data/raw/ に取得する。

- 厚労省 介護サービス情報公表システム オープンデータ（最新版 CSV、全サービス種別）
- 枚方市 介護サービス事業所一覧（Excel）
- 厚労省 医療情報ネット（ナビイ）オープンデータ（病院／診療所／歯科診療所 施設票 ZIP）

実行すると data/SOURCES.md に取得ログが追記される。
既定は介護のみ。医療側は `--target medical` で明示取得、`--target all` で両方。
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
SOURCES_LOG = ROOT / "data" / "SOURCES.md"

MHLW_PAGE = "https://www.mhlw.go.jp/stf/kaigo-kouhyou_opendata.html"
HIRAKATA_PAGE = "https://www.city.hirakata.osaka.jp/0000037120.html"
MHLW_MEDICAL_PAGE = (
    "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryou/newpage_43373.html"
)

# 医療情報ネット（ナビイ）施設票 ZIP の命名規則。
#   01-1 = 病院、02-1 = 一般診療所、03-1 = 歯科診療所
#   /content/11121000/{code}_{kind}_facility_info_YYYYMMDD.zip
MEDICAL_FACILITY_PATTERN = re.compile(
    r"/content/11121000/(?P<code>0[123])-1_(?P<kind>hospital|clinic|dental)"
    r"_facility_info_(?P<date>\d{8})\.zip$"
)
MEDICAL_KIND_LABEL = {
    "hospital": "病院",
    "clinic": "一般診療所",
    "dental": "歯科診療所",
}

USER_AGENT = "hukushimap/0.1 (personal research)"
REQUEST_INTERVAL_SEC = 1.0
TIMEOUT_SEC = 60

JST = timezone(timedelta(hours=9))


@dataclass
class Downloaded:
    source: str
    label: str
    url: str
    path: Path
    size_bytes: int


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def _get_html(session: requests.Session, url: str) -> BeautifulSoup:
    r = session.get(url, timeout=TIMEOUT_SEC)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    return BeautifulSoup(r.text, "html.parser")


def _download(session: requests.Session, url: str, dest: Path) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with session.get(url, timeout=TIMEOUT_SEC, stream=True) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)
    return dest.stat().st_size


def fetch_mhlw(out_dir: Path) -> list[Downloaded]:
    out_dir.mkdir(parents=True, exist_ok=True)
    session = _session()
    soup = _get_html(session, MHLW_PAGE)

    # 最新版の命名規則: /content/12300000/jigyosho_{3桁コード}.csv
    pattern = re.compile(r"/content/12300000/jigyosho_(\d{3})\.csv$")
    latest: dict[str, str] = {}
    for a in soup.find_all("a", href=True):
        m = pattern.search(a["href"])
        if m and m.group(1) not in latest:
            latest[m.group(1)] = urljoin(MHLW_PAGE, a["href"])

    if not latest:
        raise RuntimeError(
            f"厚労省ページから最新版CSVリンクが見つかりません: {MHLW_PAGE}"
        )

    results: list[Downloaded] = []
    for code in sorted(latest):
        url = latest[code]
        dest = out_dir / f"jigyosho_{code}.csv"
        if dest.exists() and dest.stat().st_size > 0:
            print(f"[mhlw] {code} -> {dest.relative_to(ROOT)} (skip, exists)")
            results.append(
                Downloaded("mhlw", code, url, dest, dest.stat().st_size)
            )
            continue
        print(f"[mhlw] {code} -> {dest.relative_to(ROOT)}")
        size = _download(session, url, dest)
        results.append(Downloaded("mhlw", code, url, dest, size))
        time.sleep(REQUEST_INTERVAL_SEC)
    return results


def fetch_hirakata(out_dir: Path) -> Downloaded:
    out_dir.mkdir(parents=True, exist_ok=True)
    session = _session()
    soup = _get_html(session, HIRAKATA_PAGE)

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.lower().endswith(".xlsx"):
            continue
        if "care_service" not in href.lower():
            continue
        url = urljoin(HIRAKATA_PAGE, href)
        dest = out_dir / Path(href).name
        label = a.get_text(strip=True) or Path(href).name
        if dest.exists() and dest.stat().st_size > 0:
            print(f"[hirakata] {label} -> {dest.relative_to(ROOT)} (skip, exists)")
            return Downloaded(
                "hirakata", label, url, dest, dest.stat().st_size
            )
        print(f"[hirakata] {label} -> {dest.relative_to(ROOT)}")
        size = _download(session, url, dest)
        return Downloaded("hirakata", label, url, dest, size)

    raise RuntimeError(
        f"枚方市ページから事業所一覧xlsxリンクが見つかりません: {HIRAKATA_PAGE}"
    )


def fetch_mhlw_medical(out_dir: Path) -> list[Downloaded]:
    """医療情報ネット（ナビイ）施設票 ZIP を kind ごとに最新日付のみ取得し、CSV を展開する。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    session = _session()
    soup = _get_html(session, MHLW_MEDICAL_PAGE)

    # kind ごとに最新日付を選ぶ（ページには複数期分載っているため）
    latest: dict[str, tuple[str, str]] = {}  # kind -> (date, absolute_url)
    for a in soup.find_all("a", href=True):
        m = MEDICAL_FACILITY_PATTERN.search(a["href"])
        if not m:
            continue
        kind = m.group("kind")
        date = m.group("date")
        url = urljoin(MHLW_MEDICAL_PAGE, a["href"])
        if kind not in latest or date > latest[kind][0]:
            latest[kind] = (date, url)

    expected = {"hospital", "clinic", "dental"}
    missing = expected - set(latest)
    if missing:
        raise RuntimeError(
            f"医療情報ネットから施設票リンクが見つかりません: {missing} / {MHLW_MEDICAL_PAGE}"
        )

    results: list[Downloaded] = []
    for kind in ("hospital", "clinic", "dental"):
        date, url = latest[kind]
        zip_dest = out_dir / f"{kind}_facility_info_{date}.zip"
        if zip_dest.exists() and zip_dest.stat().st_size > 0:
            print(f"[medical] {kind} {date} -> {zip_dest.relative_to(ROOT)} (skip, exists)")
            size = zip_dest.stat().st_size
        else:
            print(f"[medical] {kind} {date} -> {zip_dest.relative_to(ROOT)}")
            size = _download(session, url, zip_dest)
            time.sleep(REQUEST_INTERVAL_SEC)

        # ZIP 内の CSV を同ディレクトリに展開（名称は kind 固定にして normalize 側で参照しやすく）
        csv_dest = out_dir / f"{kind}_facility_info.csv"
        _extract_single_csv(zip_dest, csv_dest)

        results.append(
            Downloaded("medical", f"{MEDICAL_KIND_LABEL[kind]}施設票 ({date})", url, zip_dest, size)
        )
    return results


def _extract_single_csv(zip_path: Path, csv_dest: Path) -> None:
    """ZIP 内の単一 CSV を固定名で展開。既に同サイズ同 mtime なら上書きしない。"""
    with zipfile.ZipFile(zip_path) as zf:
        csvs = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if len(csvs) != 1:
            raise RuntimeError(f"{zip_path.name}: CSV 1 本以外の構成は未対応 ({csvs})")
        with zf.open(csvs[0]) as src, csv_dest.open("wb") as dst:
            while True:
                chunk = src.read(64 * 1024)
                if not chunk:
                    break
                dst.write(chunk)


def append_sources_log(items: list[Downloaded]) -> None:
    if not items:
        return

    titles = {
        "mhlw": "A. 厚労省 介護サービス情報公表システム オープンデータ",
        "hirakata": "B. 枚方市 介護サービス事業所一覧",
        "medical": "N. 厚労省 医療情報ネット（ナビイ）オープンデータ",
    }
    grouped: dict[str, list[Downloaded]] = {}
    for it in items:
        grouped.setdefault(it.source, []).append(it)

    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M %Z")
    lines = [f"\n### {now}", ""]
    for key in ("mhlw", "hirakata", "medical"):
        if key not in grouped:
            continue
        lines.append(f"#### {titles[key]}")
        lines.append("")
        for it in grouped[key]:
            rel = it.path.relative_to(ROOT)
            size_kb = it.size_bytes / 1024
            lines.append(f"- `{rel}` ({size_kb:,.1f} KB) — <{it.url}>")
        lines.append("")

    with SOURCES_LOG.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        choices=("care", "medical", "all"),
        default="care",
        help="取得対象。care=介護（既定・既存挙動）, medical=医療情報ネットのみ, all=両方",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    all_items: list[Downloaded] = []

    if args.target in ("care", "all"):
        print("== MHLW (介護) ==")
        mhlw = fetch_mhlw(RAW_DIR / "mhlw")
        print(f"  downloaded {len(mhlw)} files")
        all_items.extend(mhlw)

        print("== Hirakata ==")
        hirakata = [fetch_hirakata(RAW_DIR / "hirakata")]
        print(f"  downloaded {len(hirakata)} files")
        all_items.extend(hirakata)

    if args.target in ("medical", "all"):
        print("== MHLW 医療情報ネット（ナビイ） ==")
        medical = fetch_mhlw_medical(RAW_DIR / "mhlw_medical")
        print(f"  downloaded {len(medical)} files")
        all_items.extend(medical)

    append_sources_log(all_items)
    print(
        f"\nTotal {len(all_items)} files. Log appended to "
        f"{SOURCES_LOG.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
