import json
import pathlib

for p in sorted(pathlib.Path("samples").glob("*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    print("===", p.name, "mode=", d["mode"], "n=", len(d["importers"]))
    for i in d["importers"]:
        email = i.get("contact_email") or "-"
        site = (i.get("website") or "-")[:45]
        name = i["company_name"][:48]
        print(f"  {i['rank']}. {name} | {i['relevance_score']} | {email} | {site}")
