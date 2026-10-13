$ErrorActionPreference = "Stop"

if (-not $env:KOMPASS_EXPORT_TOKEN) {
    Write-Error "KOMPASS_EXPORT_TOKEN saknas."
    exit 1
}

$url = "https://kompass26.se/api/fokus/export?token=$($env:KOMPASS_EXPORT_TOKEN)"
$tempFile = Join-Path $env:TEMP "kompass26-fokus-svar.csv"
$jsonFile = "data\fokus_svar.json"

try {
    Write-Host "Hamtar enkatsvar fran Kompass26..."

    Invoke-WebRequest `
        -Uri $url `
        -OutFile $tempFile

    Write-Host "Validerar och skapar JSON..."

    py scripts\csv_to_fokus_json.py `
        $tempFile `
        $jsonFile

    if ($LASTEXITCODE -ne 0) {
        throw "Python-konverteringen misslyckades."
    }

    # Las den nya JSON-filen.
    $newData = Get-Content $jsonFile -Raw -Encoding UTF8 |
        ConvertFrom-Json

    $newCount = @($newData.responses).Count

    Write-Host ""
    Write-Host "Antal svar i statistiken: $newCount"

    # Kontrollera hela Hugo-bygget innan nagot publiceras.
    Write-Host ""
    Write-Host "Kontrollerar Hugo-bygget..."

    hugo --minify

    if ($LASTEXITCODE -ne 0) {
        throw "Hugo-bygget misslyckades."
    }

    Write-Host ""
    Write-Host "Hugo-bygget lyckades."

    # Visa aven andra lokala andringar, men lagg inte till dem.
    Write-Host ""
    Write-Host "Git-status:"
    git status --short

    Write-Host ""
    Write-Host "andring i resultatfilen:"
    git diff --stat -- $jsonFile

    # Kontrollera om resultatfilen skiljer sig fran Git-versionen.
    git diff --quiet -- $jsonFile

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Resultatfilen har inte andrats."
        Write-Host "Inget behover publiceras."
        exit 0
    }

    Write-Host ""
    $answer = Read-Host "Publicera den nya resultatfilen? (J/N)"

    if ($answer -notmatch '^[Jj]$') {
        Write-Host ""
        Write-Host "Ingen publicering gjordes."
        exit 0
    }

    # Lagg endast resultatfilen i denna commit.
    git add -- $jsonFile

    git commit -m "Update focus survey results"

    if ($LASTEXITCODE -ne 0) {
        throw "Git commit misslyckades."
    }

    git push

    if ($LASTEXITCODE -ne 0) {
        throw "Git push misslyckades. Commits finns kvar lokalt."
    }

    Write-Host ""
    Write-Host "Klart. Resultaten har pushats till GitHub."
}
catch {
    Write-Host ""
    Write-Host "FEL: Uppdateringen avbrots."
    Write-Host $_.Exception.Message
    Write-Host ""
    Write-Host "Ingen automatisk publicering har gjorts."
    exit 1
}
finally {
    if (Test-Path $tempFile) {
        Remove-Item $tempFile
    }
}