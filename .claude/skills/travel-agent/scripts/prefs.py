#!/usr/bin/env python3
"""Travel profile store for the travel-agent skill.

Keeps one JSON file so preferences, past trips and price watches survive between
conversations. Doing this in a script (not by hand-editing JSON) keeps the file
valid and the updates small.

Location: $TRAVEL_AGENT_HOME/profile.json, else <skill>/memory/profile.json.

Usage:
  prefs.py show                       # print whole profile
  prefs.py get flights.cabin          # print one value (dotted path)
  prefs.py set flights.cabin economy  # set scalar (JSON accepted: '["LHR","LGW"]')
  prefs.py add hotels.must_have "free cancellation"   # append to a list (no dupes)
  prefs.py remove hotels.must_have "free cancellation"
  prefs.py learn "Hates red-eye flights" --source "rejected 3 night flights" --confidence high
  prefs.py forget "red-eye"           # drop learned items containing text
  prefs.py trip "Lisbon, Mar 2026" --rating 5 --notes "loved Alfama, hotel too noisy"
  prefs.py watch add LHR-JFK --depart 2026-12-10 --return 2026-12-17 --target 450 --currency GBP
  prefs.py watch list | prefs.py watch remove <id>
  prefs.py path                       # where the file lives
"""
import argparse, json, os, sys, datetime, uuid
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
HOME = Path(os.environ.get("TRAVEL_AGENT_HOME", SKILL_DIR / "memory"))
FILE = HOME / "profile.json"

TEMPLATE = {
    "version": 1,
    "identity": {"home_airports": [], "nationalities": [], "currency": None,
                 "loyalty_programs": [], "cards_with_travel_perks": [], "travelling_with": None},
    "budget": {"style": None, "notes": None},
    "flights": {"cabin": None, "max_stops": None, "avoid_airlines": [], "prefer_airlines": [],
                "seat": None, "avoid": [], "bags": None},
    "hotels": {"min_rating": None, "types": [], "must_have": [], "avoid": [], "location_pref": None},
    "cars": {"class": None, "transmission": None, "must_have": [], "avoid_suppliers": []},
    "style": {"pace": None, "interests": [], "food": [], "dislikes": []},
    "learned": [],   # observed preferences: {text, confidence, source, date}
    "trips": [],     # past trips and how they went
    "watches": [],   # price watches
}


def load():
    if FILE.exists():
        return json.loads(FILE.read_text())
    return json.loads(json.dumps(TEMPLATE))


def save(d):
    HOME.mkdir(parents=True, exist_ok=True)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(FILE)


def walk(d, path, create=False):
    keys = path.split(".")
    for k in keys[:-1]:
        if k not in d:
            if not create:
                raise KeyError(path)
            d[k] = {}
        d = d[k]
    return d, keys[-1]


def parse(v):
    try:
        return json.loads(v)
    except json.JSONDecodeError:
        return v


def today():
    return datetime.date.today().isoformat()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show"); sub.add_parser("path")
    g = sub.add_parser("get"); g.add_argument("key")
    s = sub.add_parser("set"); s.add_argument("key"); s.add_argument("value")
    a = sub.add_parser("add"); a.add_argument("key"); a.add_argument("value")
    r = sub.add_parser("remove"); r.add_argument("key"); r.add_argument("value")
    l = sub.add_parser("learn"); l.add_argument("text"); l.add_argument("--source", default="")
    l.add_argument("--confidence", choices=["low", "medium", "high"], default="medium")
    f = sub.add_parser("forget"); f.add_argument("text")
    t = sub.add_parser("trip"); t.add_argument("name"); t.add_argument("--rating", type=int)
    t.add_argument("--notes", default="")
    w = sub.add_parser("watch"); ws = w.add_subparsers(dest="wcmd", required=True)
    wa = ws.add_parser("add"); wa.add_argument("route"); wa.add_argument("--depart")
    wa.add_argument("--return", dest="ret"); wa.add_argument("--target", type=float)
    wa.add_argument("--currency", default="")
    ws.add_parser("list"); wr = ws.add_parser("remove"); wr.add_argument("id")
    args = p.parse_args()

    if args.cmd == "path":
        print(FILE); return
    d = load()

    if args.cmd == "show":
        print(json.dumps(d, indent=2, ensure_ascii=False)); return
    if args.cmd == "get":
        parent, k = walk(d, args.key)
        print(json.dumps(parent[k], indent=2, ensure_ascii=False)); return
    if args.cmd == "set":
        parent, k = walk(d, args.key, create=True); parent[k] = parse(args.value)
    elif args.cmd == "add":
        parent, k = walk(d, args.key, create=True)
        lst = parent.setdefault(k, [])
        if not isinstance(lst, list):
            sys.exit(f"{args.key} is not a list")
        v = parse(args.value)
        if v not in lst:
            lst.append(v)
    elif args.cmd == "remove":
        parent, k = walk(d, args.key)
        v = parse(args.value)
        parent[k] = [x for x in parent[k] if x != v and x != args.value]
    elif args.cmd == "learn":
        # Reinforce an existing note rather than duplicating it.
        for x in d["learned"]:
            if x["text"].lower() == args.text.lower():
                x.update(confidence=args.confidence, date=today())
                if args.source: x["source"] = args.source
                break
        else:
            d["learned"].append({"text": args.text, "confidence": args.confidence,
                                 "source": args.source, "date": today()})
    elif args.cmd == "forget":
        n = len(d["learned"])
        d["learned"] = [x for x in d["learned"] if args.text.lower() not in x["text"].lower()]
        print(f"removed {n - len(d['learned'])} learned item(s)")
    elif args.cmd == "trip":
        d["trips"].append({"name": args.name, "rating": args.rating, "notes": args.notes, "date": today()})
    elif args.cmd == "watch":
        if args.wcmd == "list":
            print(json.dumps(d["watches"], indent=2)); return
        if args.wcmd == "add":
            d["watches"].append({"id": uuid.uuid4().hex[:6], "route": args.route, "depart": args.depart,
                                 "return": args.ret, "target": args.target, "currency": args.currency,
                                 "created": today(), "last_seen_price": None})
        else:
            d["watches"] = [x for x in d["watches"] if x["id"] != args.id]
    save(d)
    print("ok")


if __name__ == "__main__":
    main()
