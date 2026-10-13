#!/usr/bin/env python3

import csv
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ALLOWED = {
    "viktigast": {"a", "b", "c", "d"},
    "omraden": {"a", "b", "c", "d", "e", "f", "g", "h"},
    "pastaende": {"a", "b", "c", "d"},
    "sjalvbild": {"a", "b", "c", "d"},
}

REQUIRED_COLUMNS = {
    "id",
    "submitted_at",
    "viktigast",
    "omraden",
    "pastaende",
    "sjalvbild",
    "kommentar",
}


def split_ids(value):
    if not value:
        return []

    return [
        item.strip()
        for item in value.split(";")
        if item.strip()
    ]


def validate_single(value, field, row_number):
    if value not in ALLOWED[field]:
        raise ValueError(
            f"Rad {row_number}: ogiltigt värde "
            f"{value!r} i {field}."
        )


def validate_multiple(values, field, row_number):
    invalid = [
        value
        for value in values
        if value not in ALLOWED[field]
    ]

    if invalid:
        raise ValueError(
            f"Rad {row_number}: ogiltigt värde "
            f"{invalid!r} i {field}."
        )

    if len(values) != len(set(values)):
        raise ValueError(
            f"Rad {row_number}: samma alternativ förekommer "
            f"flera gånger i {field}."
        )


def main():
    if len(sys.argv) not in (2, 3):
        print(
            "Användning: "
            "py csv_to_fokus_json.py "
            "<fokus-svar.csv> [output.json]"
        )
        sys.exit(2)

    source = Path(sys.argv[1])

    destination = (
        Path(sys.argv[2])
        if len(sys.argv) == 3
        else Path("data/fokus_svar.json")
    )

    if not source.exists():
        print(f"FEL: CSV-filen finns inte: {source}")
        sys.exit(1)

    try:
        with source.open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as f:

            reader = csv.DictReader(f)

            columns = set(reader.fieldnames or [])

            missing = REQUIRED_COLUMNS - columns

            if missing:
                raise ValueError(
                    "CSV-filen saknar kolumner: "
                    + ", ".join(sorted(missing))
                )

            responses = []
            seen_ids = set()

            for row_number, row in enumerate(reader, start=2):

                try:
                    response_id = int(row["id"])
                except (TypeError, ValueError):
                    raise ValueError(
                        f"Rad {row_number}: ogiltigt id "
                        f"{row['id']!r}."
                    )

                if response_id in seen_ids:
                    raise ValueError(
                        f"Rad {row_number}: id {response_id} "
                        "förekommer flera gånger."
                    )

                seen_ids.add(response_id)

                viktigast = row["viktigast"].strip()
                omraden = split_ids(row["omraden"])
                pastaende = split_ids(row["pastaende"])
                sjalvbild = row["sjalvbild"].strip()

                validate_single(
                    viktigast,
                    "viktigast",
                    row_number
                )

                validate_multiple(
                    omraden,
                    "omraden",
                    row_number
                )

                validate_multiple(
                    pastaende,
                    "pastaende",
                    row_number
                )

                validate_single(
                    sjalvbild,
                    "sjalvbild",
                    row_number
                )

                responses.append({
                    "id": response_id,
                    "submitted_at":
                        row["submitted_at"].strip(),
                    "viktigast": viktigast,
                    "omraden": omraden,
                    "pastaende": pastaende,
                    "sjalvbild": sjalvbild,
                    "kommentar":
                        row["kommentar"] or "",
                })

        if not responses:
            raise ValueError(
                "CSV-filen innehåller inga enkätsvar."
            )

        # Skriv först när ALL data har validerats.
        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        temp_file = destination.with_suffix(".tmp")

        output = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "responses": responses,
        }

        with temp_file.open(
            "w",
            encoding="utf-8",
            newline="\n"
        ) as f:
            json.dump(
                output,
                f,
                ensure_ascii=False,
                indent=2
            )
            f.write("\n")

        # Ersätt den gamla JSON-filen först nu.
        temp_file.replace(destination)

        print(
            f"OK: {len(responses)} svar validerades."
        )
        print(
            f"Skrev: {destination}"
        )

    except (
        csv.Error,
        UnicodeError,
        ValueError,
        OSError
    ) as error:

        print()
        print("FEL: Konverteringen avbröts.")
        print(error)
        print()
        print(
            "Den befintliga JSON-filen har inte "
            "skrivits över."
        )

        sys.exit(1)


if __name__ == "__main__":
    main()