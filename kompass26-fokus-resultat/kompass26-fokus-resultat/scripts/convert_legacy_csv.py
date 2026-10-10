#!/usr/bin/env python3
"""Convert the current Swedish-label CSV export to the new ID-based format."""
from pathlib import Path
import csv
import argparse

Q1 = {"Europaparlamentet":"a","Riksdagen":"b","Regionfullmäktige":"c","Kommunfullmäktige":"d"}
Q2 = {"Ekonomi och jobb":"a","Försvar och beredskap":"b","Migration och integration":"c","Miljö och klimat":"d","Kriminalitet":"e","Sjukvård och omsorg":"f","Skola och utbildning":"g","Infrastruktur: bostäder, energi, transporter, kommunikation":"h"}
Q3 = {"Sverige är ett bra land att leva i.":"a","Sverige mår bra av invandring.":"b","Ukrainas kamp är viktig för Sveriges säkerhet.":"c","Sveriges utmaningar kräver kompromisser.":"d"}
Q4 = {"Jag är orolig för framtiden.":"a","Jag bygger framtiden.":"b","Jag blir arg när jag ser fel och orättvisor.":"c","Jag har idéer om vad som kan göras.":"d"}

def norm(s):
    if s is None: return ""
    return str(s).strip()

def conv_multi(value, mapping):
    parts = [p.strip() for p in norm(value).split(";") if p.strip()]
    return ";".join(mapping.get(p, p) for p in parts)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args=ap.parse_args()
    with args.input.open("r", encoding="utf-8-sig", newline="") as f:
        rows=list(csv.DictReader(f))
    fields=["id","submitted_at","viktigast","omraden","pastaende","sjalvbild","kommentar"]
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        w=csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            # Handle both correctly decoded exports and mojibake introduced by a bad opening.
            w.writerow({
                "id": r.get("id", "").replace('ï»¿"', '').replace('"',''),
                "submitted_at": r.get("submitted_at", ""),
                "viktigast": Q1.get(norm(r.get("viktigast")), norm(r.get("viktigast"))),
                "omraden": conv_multi(r.get("omraden", ""), Q2),
                "pastaende": conv_multi(r.get("pastaende", ""), Q3),
                "sjalvbild": Q4.get(norm(r.get("sjalvbild")), norm(r.get("sjalvbild"))),
                "kommentar": r.get("kommentar", "")
            })
    print(args.output)

if __name__ == "__main__":
    main()
