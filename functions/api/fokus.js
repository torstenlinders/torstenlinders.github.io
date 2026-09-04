export async function onRequestPost(context) {
  const data = await context.request.json();

  console.log("Fokus submission:", data);

  return new Response(
    JSON.stringify({ ok: true }),
    {
      status: 200,
      headers: {
        "Content-Type": "application/json"
      }
    }
  );
}