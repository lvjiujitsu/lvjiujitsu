"""Auditoria de scroll mobile headless.

Percorre as principais rotas no viewport iPhone 12, mede:
- scrollHeight vs innerHeight do documento
- se há overflow escondido em ancestrais que impedem scroll
- se algum elemento fixed está interceptando toques no centro

Reporta rotas onde há conteúdo recortado ou scroll travado.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
USER = "admin"
PASSWORD = "admin"

ROUTES = [
    ("login", "/login/"),
    ("admin-home", "/home/admin/"),
    ("admin-calendar", "/admin-calendar/"),
    ("person-list", "/people/"),
    ("person-type-list", "/person-types/"),
    ("class-category-list", "/class-categories/"),
    ("class-group-list", "/class-groups/"),
    ("class-schedule-list", "/class-schedules/"),
    ("product-list", "/products/"),
    ("product-catalog", "/materials/"),
    ("plan-list", "/plans/"),
    ("plan-catalog", "/plans-catalog/"),
]


AUDIT_JS = """
() => {
  const doc = document.documentElement;
  const body = document.body;
  const info = {
    innerHeight: window.innerHeight,
    docScrollHeight: doc.scrollHeight,
    bodyScrollHeight: body.scrollHeight,
    bodyOverflow: getComputedStyle(body).overflow,
    bodyOverflowY: getComputedStyle(body).overflowY,
    htmlOverflow: getComputedStyle(doc).overflow,
    htmlOverflowY: getComputedStyle(doc).overflowY,
    pageShellHeight: 0,
    pageShellOverflow: '',
    contentShellHeight: 0,
    blockers: [],
  };
  const shell = document.querySelector('.page-shell');
  if (shell) {
    info.pageShellHeight = shell.scrollHeight;
    info.pageShellOverflow = getComputedStyle(shell).overflow;
  }
  const cs = document.querySelector('.content-shell');
  if (cs) {
    info.contentShellHeight = cs.scrollHeight;
  }
  // Elementos position:fixed cobrindo a viewport
  document.querySelectorAll('*').forEach((el) => {
    const st = getComputedStyle(el);
    if ((st.position === 'fixed' || st.position === 'absolute')) {
      const r = el.getBoundingClientRect();
      if (
        r.width >= window.innerWidth * 0.9 &&
        r.height >= window.innerHeight * 0.9 &&
        st.display !== 'none' &&
        st.visibility !== 'hidden' &&
        parseFloat(st.opacity || '1') > 0 &&
        st.pointerEvents !== 'none'
      ) {
        info.blockers.push({
          tag: el.tagName,
          id: el.id,
          cls: el.className ? String(el.className).slice(0, 120) : '',
          pos: st.position,
          z: st.zIndex,
          w: Math.round(r.width),
          h: Math.round(r.height),
        });
      }
    }
  });
  return info;
}
"""


def main():
    results = []
    out_dir = Path("scripts/audit_out")
    out_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        iphone = p.devices["iPhone 12"]
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(**iphone)
        page = context.new_page()

        # login
        page.goto(f"{BASE}/login/")
        page.fill('input[name="identifier"]', USER)
        page.fill('input[name="password"]', PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")

        for name, path in ROUTES:
            url = f"{BASE}{path}"
            try:
                page.goto(url, wait_until="networkidle")
            except Exception as e:
                results.append({"route": name, "path": path, "error": str(e)})
                continue

            info = page.evaluate(AUDIT_JS)
            info["route"] = name
            info["path"] = path
            info["overflow_cut"] = info["docScrollHeight"] > info["innerHeight"] + 4
            info["has_blocker"] = len(info["blockers"]) > 0
            # Try to scroll to bottom and see if scroll position actually moves
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(100)
            final_y = page.evaluate("window.scrollY")
            info["final_scrollY"] = final_y
            expected = max(0, info["docScrollHeight"] - info["innerHeight"])
            info["expected_scrollY"] = expected
            info["scroll_works"] = final_y >= expected - 4 if expected > 0 else True
            results.append(info)
            page.screenshot(path=str(out_dir / f"{name}.png"), full_page=True)
            # Reset
            page.evaluate("window.scrollTo(0, 0)")

        browser.close()

    (out_dir / "report.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    summary = []
    for r in results:
        summary.append(
            f"{r['route']:20s} inner={r.get('innerHeight')} "
            f"doc={r.get('docScrollHeight')} "
            f"finalY={r.get('final_scrollY')} expY={r.get('expected_scrollY')} "
            f"scroll_ok={r.get('scroll_works')} blockers={len(r.get('blockers',[]))}"
        )
    print("\n".join(summary))
    problems = [
        r for r in results
        if r.get("has_blocker")
        or r.get("bodyOverflow") == "hidden"
        or r.get("htmlOverflow") == "hidden"
        or r.get("scroll_works") is False
    ]
    if problems:
        print("\n=== PROBLEMAS ENCONTRADOS ===")
        for pr in problems:
            print(f"- {pr['route']}: blockers={pr.get('blockers')} body={pr.get('bodyOverflow')} html={pr.get('htmlOverflow')}")
        sys.exit(1)
    print("\nOK — nenhuma rota com bloqueador óbvio de scroll.")


if __name__ == "__main__":
    main()
