export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // CSV-export: exportera språkneutrala ID:n.
    // Översättning sker vid publicering, inte i datalagret.
    if (
      request.method === "GET" &&
      url.pathname === "/api/fokus/export"
    ) {
      const token = url.searchParams.get("token");

      if (!token || token !== env.EXPORT_TOKEN) {
        return new Response("Unauthorized", { status: 401 });
      }

      const result = await env.DB
        .prepare(`
          SELECT
            id,
            submitted_at,
            viktigast,
            omraden,
            pastaende,
            sjalvbild,
            kommentar
          FROM fokus_responses
          ORDER BY id
        `)
        .all();

      const rows = result.results || [];

      function csvEscape(value) {
        if (value === null || value === undefined) {
          return "";
        }

        const text = String(value).replace(/"/g, '""');
        return `"${text}"`;
      }

      const header = [
        "id",
        "submitted_at",
        "viktigast",
        "omraden",
        "pastaende",
        "sjalvbild",
        "kommentar"
      ];

      const csvLines = [header.map(csvEscape).join(",")];

      for (const row of rows) {
        const omraden = JSON.parse(row.omraden || "[]");
        const pastaende = JSON.parse(row.pastaende || "[]");

        csvLines.push(
          [
            row.id,
            row.submitted_at,
            row.viktigast,
            omraden.join(";"),
            pastaende.join(";"),
            row.sjalvbild,
            row.kommentar
          ]
            .map(csvEscape)
            .join(",")
        );
      }

      const csv = "\uFEFF" + csvLines.join("\r\n");

      return new Response(csv, {
        status: 200,
        headers: {
          "Content-Type": "text/csv; charset=utf-8",
          "Content-Disposition": 'attachment; filename="fokus-svar.csv"'
        }
      });
    }

    // Enkätsvar
    if (
      request.method === "POST" &&
      url.pathname === "/api/fokus"
    ) {
      try {
        const data = await request.json();
        const token = data.turnstileToken;

        if (!token) {
          return new Response(
            JSON.stringify({ ok: false, error: "missing_turnstile" }),
            {
              status: 400,
              headers: { "Content-Type": "application/json" }
            }
          );
        }

        const verifyResponse = await fetch(
          "https://challenges.cloudflare.com/turnstile/v0/siteverify",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/x-www-form-urlencoded"
            },
            body: new URLSearchParams({
              secret: env.TURNSTILE_SECRET,
              response: token
            })
          }
        );

        const verifyResult = await verifyResponse.json();

        if (!verifyResult.success) {
          console.error("Turnstile verification failed:", verifyResult);

          return new Response(
            JSON.stringify({
              ok: false,
              error: "turnstile_failed",
              turnstileErrors: verifyResult["error-codes"]
            }),
            {
              status: 403,
              headers: { "Content-Type": "application/json" }
            }
          );
        }

        const allowedViktigast = ["a", "b", "c", "d"];
        const allowedOmraden = ["a", "b", "c", "d", "e", "f", "g", "h"];
        const allowedPastaende = ["a", "b", "c", "d"];
        const allowedSjalvbild = ["a", "b", "c", "d"];

        if (!allowedViktigast.includes(data.viktigast)) {
          return new Response(
            JSON.stringify({ ok: false, error: "invalid_viktigast" }),
            { status: 400, headers: { "Content-Type": "application/json" } }
          );
        }

        if (
          !Array.isArray(data.omraden) ||
          !data.omraden.every((value) => allowedOmraden.includes(value))
        ) {
          return new Response(
            JSON.stringify({ ok: false, error: "invalid_omraden" }),
            { status: 400, headers: { "Content-Type": "application/json" } }
          );
        }

        if (
          !Array.isArray(data.pastaende) ||
          !data.pastaende.every((value) => allowedPastaende.includes(value))
        ) {
          return new Response(
            JSON.stringify({ ok: false, error: "invalid_pastaende" }),
            { status: 400, headers: { "Content-Type": "application/json" } }
          );
        }

        if (!allowedSjalvbild.includes(data.sjalvbild)) {
          return new Response(
            JSON.stringify({ ok: false, error: "invalid_sjalvbild" }),
            { status: 400, headers: { "Content-Type": "application/json" } }
          );
        }

        const kommentar =
          typeof data.kommentar === "string"
            ? data.kommentar.trim().slice(0, 2000)
            : "";

        await env.DB
          .prepare(`
            INSERT INTO fokus_responses
              (submitted_at, viktigast, omraden, pastaende, sjalvbild, kommentar)
            VALUES (?, ?, ?, ?, ?, ?)
          `)
          .bind(
            new Date().toISOString(),
            data.viktigast,
            JSON.stringify(data.omraden),
            JSON.stringify(data.pastaende ?? []),
            data.sjalvbild ?? null,
            kommentar
          )
          .run();

        return new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        });
      } catch (error) {
        console.error("Fokus error:", error);

        return new Response(JSON.stringify({ ok: false }), {
          status: 500,
          headers: { "Content-Type": "application/json" }
        });
      }
    }

    return new Response("Not found", { status: 404 });
  }
};
