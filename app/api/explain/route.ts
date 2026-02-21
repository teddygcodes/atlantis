import { generateText } from "ai";

export async function POST(req: Request) {
  const { text, type } = await req.json();

  if (!text || typeof text !== "string") {
    return Response.json({ error: "Missing text" }, { status: 400 });
  }

  const label = type || "academic text";

  const { text: explanation } = await generateText({
    model: "anthropic/claude-haiku-4-5-20251001",
    system: `You explain complex academic ${label} in simple everyday English that a high schooler would understand. Keep it to 2-3 sentences. No jargon. Be clear and direct.`,
    prompt: text,
    maxOutputTokens: 300,
    temperature: 0.5,
  });

  return Response.json({ explanation });
}
