export async function POST(req: Request) {
  try {
    const { text, type } = await req.json();

    if (!text || typeof text !== "string") {
      return Response.json({ error: "Missing text" }, { status: 400 });
    }

    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      throw new Error("ANTHROPIC_API_KEY is not configured");
    }

    const label = type || "academic text";
    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
      },
      body: JSON.stringify({
        model: "claude-sonnet-4-20250514",
        max_tokens: 180,
        system: `You explain complex academic ${label} in simple everyday English that a high schooler would understand. Keep it to 2-3 sentences. No jargon. Be clear and direct.`,
        messages: [{ role: "user", content: text }],
      }),
    });

    const data = (await response.json()) as {
      content?: Array<{ type?: string; text?: string }>;
      error?: { message?: string };
    };

    if (!response.ok) {
      throw new Error(data.error?.message || "Failed to generate explanation");
    }

    const explanation = data.content?.find((item) => item.type === "text")?.text;

    if (!explanation) {
      throw new Error("No explanation returned");
    }

    return Response.json({ explanation });
  } catch (error) {
    const details =
      process.env.NODE_ENV === "development" && error instanceof Error
        ? error.message
        : undefined;

    return Response.json(
      {
        error: "Failed to generate explanation",
        details,
      },
      { status: 500 }
    );
  }
}
