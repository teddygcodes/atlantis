import { generateText } from "ai";
import { anthropic } from "@ai-sdk/anthropic";

export async function POST(req: Request) {
  try {
    const { text, type } = await req.json();

    if (!text || typeof text !== "string") {
      return Response.json({ error: "Missing text" }, { status: 400 });
    }

    const label = type || "academic text";

    const result = await generateText({
      model: anthropic("claude-sonnet-4-20250514"),
      system: `You explain complex academic ${label} in simple everyday English that a high schooler would understand. Keep it to 2-3 sentences. No jargon. Be clear and direct.`,
      prompt: text,
    });

    return Response.json({ explanation: result.text });
  } catch (error) {
    return Response.json(
      { error: "Failed to generate explanation" },
      { status: 500 }
    );
  }
}
