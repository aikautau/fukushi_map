"""各ソースから介護事業所データを data/raw/ に取得する。

- 厚労省 介護サービス情報公表システム オープンデータ（最新版 CSV、全サービス種別）
- 枚方市 介護サービス事業所一覧（Excel）

実行すると data/SOURCES.md に取得ログが追記される。
"""

from __future__ import annotations

import re
import sys
import time
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


def append_sources_log(items: list[Downloaded]) -> None:
    if not items:
        return

    titles = {
        "mhlw": "A. 厚労省 介護サービス情報公表システム オープンデータ",
        "hirakata": "B. 枚方市 介護サービス事業所一覧",
    }
    grouped: dict[str, list[Downloaded]] = {}
    for it in items:
        grouped.setdefault(it.source, []).append(it)

    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M %Z")
    lines = [f"\n### {now}", ""]
    for key in ("mhlw", "hirakata"):
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


def main() -> int:
    print("== MHLW ==")
    mhlw = fetch_mhlw(RAW_DIR / "mhlw")
    print(f"  downloaded {len(mhlw)} files")

    print("== Hirakata ==")
    hirakata = [fetch_hirakata(RAW_DIR / "hirakata")]
    print(f"  downloaded {len(hirakata)} files")

    all_items = mhlw + hirakata
    append_sources_log(all_items)
    print(
        f"\nTotal {len(all_items)} files. Log appended to "
        f"{SOURCES_LOG.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
