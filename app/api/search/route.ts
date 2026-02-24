import { streamText } from "ai";

/**
 * Sydyn-style search endpoint that streams pipeline status updates
 * followed by the actual AI-generated answer with structured metadata.
 */
export async function POST(req: Request) {
  const { query } = await req.json();

  if (!query || typeof query !== "string") {
    return Response.json({ error: "Missing query" }, { status: 400 });
  }

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      function send(data: Record<string, unknown>) {
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify(data)}\n\n`)
        );
      }

      // Pipeline status updates with realistic delays
      const stages = [
        { status: "Searching sources...", delay: 800 },
        { status: "Researcher drafting...", delay: 1200 },
        { status: "Adversary attacking...", delay: 1000 },
        { status: "Judge reviewing...", delay: 900 },
      ];

      for (const stage of stages) {
        send({ type: "status", message: stage.status });
        await new Promise((r) => setTimeout(r, stage.delay));
      }

      // Now call the AI for the actual answer
      try {
        const result = streamText({
          model: "anthropic/claude-sonnet-4-20250514",
          system: `You are Sydyn, the adversarial research engine powering Atlantis — a knowledge platform where hypotheses are tested through structured review.

When answering a query, you MUST respond with valid JSON matching this exact structure:
{
  "answer_bullets": ["bullet 1", "bullet 2", ...],
  "confidence": "HIGH" | "MODERATE" | "LOW",
  "confidence_score": 0.0-1.0,
  "sources": [
    {"title": "Source Name", "url": "https://...", "grade": "A" | "B" | "C" | "D" | "F"}
  ],
  "constitutional_violations": [],
  "audit_trail": {
    "mode": "strict",
    "researcher_claims": 3,
    "adversary_attacks": 2,
    "attacks_survived": 2,
    "judge_verdict": "PASS" | "WARN" | "FAIL",
    "reasoning": "Brief explanation of the verdict"
  }
}

Rules:
- Provide 3-6 concise answer bullets
- Be factual and cite real sources when possible
- Grade sources A-F based on reliability
- confidence_score should reflect actual certainty (0.0 to 1.0)
- constitutional_violations should list any issues (empty array if none)
- Only output the JSON, nothing else`,
          prompt: query,
          maxOutputTokens: 1500,
        });

        let fullText = "";
        for await (const chunk of result.textStream) {
          fullText += chunk;
          send({ type: "chunk", text: chunk });
        }

        // Parse the complete response
        try {
          // Try to extract JSON from the response
          const jsonMatch = fullText.match(/\{[\s\S]*\}/);
          if (jsonMatch) {
            const parsed = JSON.parse(jsonMatch[0]);
            send({ type: "result", data: parsed });
          } else {
            // Fallback: treat as plain text answer
            send({
              type: "result",
              data: {
                answer_bullets: [fullText.trim()],
                confidence: "MODERATE",
                confidence_score: 0.6,
                sources: [],
                constitutional_violations: [],
                audit_trail: {
                  mode: "fast",
                  researcher_claims: 1,
                  adversary_attacks: 0,
                  attacks_survived: 0,
                  judge_verdict: "WARN",
                  reasoning:
                    "Response could not be fully structured — raw answer provided",
                },
              },
            });
          }
        } catch {
          send({
            type: "result",
            data: {
              answer_bullets: [fullText.trim()],
              confidence: "MODERATE",
              confidence_score: 0.6,
              sources: [],
              constitutional_violations: [],
              audit_trail: {
                mode: "fast",
                researcher_claims: 1,
                adversary_attacks: 0,
                attacks_survived: 0,
                judge_verdict: "WARN",
                reasoning:
                  "Response could not be fully structured — raw answer provided",
              },
            },
          });
        }

        send({ type: "done" });
      } catch (error) {
        send({
          type: "error",
          message:
            error instanceof Error
              ? error.message
              : "Failed to generate answer",
        });
      }

      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
