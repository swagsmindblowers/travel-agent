#!/usr/bin/env python3
"""Pre-send lint for a travel answer written in Markdown.

Catches the mechanical slips a re-read misses:
  1. A table column, bullet list or paragraph that mixes currencies (e.g. £, € and $ together).
     A line that states a conversion ("USD 94 = about £73", "rate", "before conversion") is exempt.
  2. Amounts in a currency other than the answer's main one, unless the line states the conversion.
  3. Headline vs total: two non-table lines that both state a trip total ("total", "all-in",
     "together", "altogether", "in all") with ranges that don't overlap, e.g. "roughly £340"
     at the top and "£395-420" in the totals section. The headline must match the sum.
  4. Currency amounts in prose/tables with no label nearby (seen / est. / unknown / source / date).
Exit code 1 if anything is flagged. It cannot judge whether a sentence makes sense;
do the read-through for that.

Usage: check_answer.py answer.md
"""
import re, sys

CUR = {"£": "GBP", "€": "EUR", "$": "USD", "GBP": "GBP", "EUR": "EUR", "USD": "USD", "CAD": "CAD", "AUD": "AUD"}
PAT = re.compile(r"(£|€|\$|\b(?:GBP|EUR|USD|CAD|AUD)\b)\s?\d|\d[\d,\.]*\s?(€|£|\b(?:GBP|EUR|USD|CAD|AUD)\b)")
LABEL = re.compile(r"\b(seen|est\.?|estimate[d]?|unknown|not found|assumed|snapshots?|sources?|roughly|approx\.?|quote[d]?|listed|from \d)\b", re.I)


def currencies(text):
    found = set()
    for m in PAT.finditer(text):
        sym = m.group(1) or m.group(2)
        found.add(CUR.get(sym, sym))
    return found


def main(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    problems = []
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|"):
            j = i
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                j += 1
            rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines[i:j]]
            ncols = max(len(r) for r in rows)
            for c in range(ncols):
                cur = set()
                for r in rows:
                    if c < len(r):
                        cur |= currencies(r[c])
                if len(cur) > 1:
                    head = rows[0][c] if c < len(rows[0]) else str(c)
                    problems.append(f"line {i+1}: column '{head}' mixes currencies {sorted(cur)}. Convert to one currency (state the rate) or split into separate columns.")
            i = j
        else:
            i += 1

    # lists and paragraphs: a block of consecutive non-table lines that mixes currencies
    conv = re.compile(r"conver|rate|=|≈|approx|equivalent|original|before", re.I)
    block, start = [], 0
    def flush():
        if not block: return
        cur = set()
        for _, l in block:
            if not conv.search(l):
                cur |= currencies(l)
        if len(cur) > 1:
            problems.append(f"line {block[0][0]}: this list/paragraph mixes currencies {sorted(cur)}. Use one currency, or state the conversion on the same line.")
    for n, line in enumerate(lines, 1):
        if line.strip() == "" or line.lstrip().startswith(("|", "#")):
            flush(); block = []
        else:
            block.append((n, line))
    flush()

    # whole answer: options the user compares should be in the answer's main currency
    from collections import Counter
    cnt = Counter(c for l in lines for c in currencies(l))
    if len(cnt) > 1:
        main_cur = cnt.most_common(1)[0][0]
        for n, line in enumerate(lines, 1):
            if conv.search(line):
                continue
            other = currencies(line) - {main_cur}
            if other:
                problems.append(f"line {n}: amounts in {sorted(other)} but the answer is mainly in {main_cur}. Convert (state the rate) or put the original on a 'before conversion' line: {line.strip()[:80]}")

    # totals that disagree
    tot_kw = re.compile(r"\b(total|all-in|all in|together|altogether|in all|overall)\b", re.I)
    num = re.compile(r"[£€$]\s?(\d[\d,]*(?:\.\d+)?)(?:\s?[-–]\s?[£€$]?\s?(\d[\d,]*(?:\.\d+)?))?")
    totals, in_total_section = [], False
    for n, line in enumerate(lines, 1):
        if line.lstrip().startswith("#"):
            in_total_section = bool(tot_kw.search(line))
            continue
        if line.lstrip().startswith("|") or not line.strip():
            continue
        kws = [m for m in tot_kw.finditer(line)]
        found = []
        for m in num.finditer(line):
            lo = float(m.group(1).replace(",", ""))
            hi = float(m.group(2).replace(",", "")) if m.group(2) else lo
            lo, hi = min(lo, hi), max(lo, hi)
            if lo < 100:               # skip small add-ons such as taxes
                continue
            near = any(k.end() <= m.start() and m.start() - k.end() <= 60 for k in kws)
            if near or in_total_section:
                found.append((lo, hi))
        if found:                       # a line's last qualifying amount is its result
            lo, hi = found[-1]
            totals.append((n, lo, hi, line.strip()[:70]))
    flagged = False
    for i in range(len(totals)):
        for j in range(i + 1, len(totals)):
            a_, b_ = totals[i], totals[j]
            if not flagged and (a_[2] * 1.1 < b_[1] or b_[2] * 1.1 < a_[1]):
                problems.append(f"line {a_[0]} and line {b_[0]}: totals disagree ({a_[1]:.0f}-{a_[2]:.0f} vs {b_[1]:.0f}-{b_[2]:.0f}). Recompute the total from its parts and make the headline match: {a_[3]!r} / {b_[3]!r}")
                flagged = True

    # amounts with no label on the same line or the line before/after (tables count per row)
    for n, line in enumerate(lines):
        if PAT.search(line) and not line.lstrip().startswith("#"):
            window = " ".join(lines[max(0, n - 1): n + 2])
            if not LABEL.search(window):
                problems.append(f"line {n+1}: price with no seen/est./unknown label nearby: {line.strip()[:90]}")

    for p in problems:
        print("FLAG", p)
    print(f"{len(problems)} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
