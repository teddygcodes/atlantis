/**
 * Proxy to the real Sydyn backend.
 * Forwards the query and pipes the SSE stream back to the client.
 */

const SYDYN_BACKEND = "https://atlantis-production-01f2.up.railway.app/api/query";

export async function POST(req: Request) {
  const { query } = await req.json();

  if (!query || typeof query !== "string") {
    return Response.json({ error: "Missing query" }, { status: 400 });
  }

  const backendRes = await fetch(SYDYN_BACKEND, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });

  if (!backendRes.ok || !backendRes.body) {
    return Response.json(
      { error: `Backend error: ${backendRes.status}` },
      { status: backendRes.status }
    );
  }

  // Pipe the SSE stream straight through
  return new Response(backendRes.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
