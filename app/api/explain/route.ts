import { generateText } from "ai";

export async function POST(req: Request) {
  try {
    const { text, type } = await req.json();

    if (!text || typeof text !== "string") {
      return Response.json({ error: "Missing text" }, { status: 400 });
    }

    const label = type || "academic text";

    console.log("[v0] Explain API called with:", { textLength: text.length, type: label });

    const result = await generateText({
      model: "openai/gpt-4o-mini",
      system: `You explain complex academic ${label} in simple everyday English that a high schooler would understand. Keep it to 2-3 sentences. No jargon. Be clear and direct.`,
      prompt: text,
    });

    const explanation = result.text;
    console.log("[v0] Explain API result:", { explanationLength: explanation?.length });

    return Response.json({ explanation });
  } catch (error) {
    console.error("[v0] Explain API error:", error);
    return Response.json(
      { error: "Failed to generate explanation" },
      { status: 500 }
    );
  }
}
