# Kompass26: enkätsvar och tvåspråkiga resultatdiagram

Denna mapp innehåller en minimal ändring av den befintliga Hugo/Cloudflare-lösningen för att publicera enkätresultat på svenska och engelska.

## Flöde

1. Cloudflare Worker exporterar **språkneutrala ID:n** från D1.
2. CSV-filen sparas lokalt som `data/fokus-svar.csv`.
3. `scripts/build_fokus_charts.py` läser CSV + de två `fokus.md` + `sv.toml`/`en.toml`.
4. Skriptet genererar åtta SVG-filer: fyra svenska och fyra engelska.
5. Hugo-sidorna visar SVG-filerna och använder samma i18n-system för sidans UI.

## Viktigt

Den bifogade befintliga CSV-filen är en äldre export där Worker redan har översatt ID:n till svenska texter. För den filen finns `scripts/convert_legacy_csv.py` som engångskonvertering. När den nya Worker-exporten används behövs den inte längre.

## Installation i projektet

Kopiera:

- `worker.js` över din Worker-fil och publicera den via Cloudflare Workers.
- innehållet i `i18n/sv.toml` och `i18n/en.toml` till motsvarande befintliga filer.
- de två `fokus.md`-filerna över respektive språkversion, eller flytta bara front matter-fältet från `text` till `i18n` enligt exemplen.
- `layouts/fokus-results/single.html` och `layouts/partials/fokus-results.html`.
- `layouts/single-fokus-updated.html` beskriver ändringen av den befintliga enkätmallen: byt ut `{{ $question.text }}`/`{{ .text }}` mot `i18n` enligt filen.
- `content/fokus-resultat.md` och `content/en/focus/results.md`.
- `.fokus-results.css` till `assets/css/fokus-results.css` eller motsvarande statisk CSS-plats, beroende på hur ditt tema laddar CSS.
- `scripts/` lokalt; den behöver inte publiceras till sajten.

Lägg CSV-exporten i `data/fokus-svar.csv` och kör:

    python scripts/build_fokus_charts.py

Skriptet skriver SVG-filerna under `static/fokus-results/sv/` och `static/fokus-results/en/`.

## i18n för själva frågorna

De befintliga `fokus.md`-filerna lagrar i dag frågetexterna direkt. I den här lösningen pekar front matter i stället på i18n-nycklar. Lägg till nycklarna från `i18n-additions-sv.toml` och `i18n-additions-en.toml` i era befintliga TOML-filer. Sedan använder den uppdaterade `single.html` samma nycklar. På så sätt är fråge-/svarstexterna, och därmed även diagrammens rubriker och etiketter, språkstyrda via i18n.

## Uppdatering av data

Efter publicering av den nya Worker-versionen: hämta `fokus-svar.csv` på samma sätt som tidigare och ersätt `data/fokus-svar.csv`. Kör sedan byggskriptet igen.
