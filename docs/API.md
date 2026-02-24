# API Documentation

## Overview

The Atlantis API provides a single endpoint for generating plain-language explanations of scientific hypotheses and academic content.

---

## Endpoints

### POST /api/explain

Generates a simple, accessible explanation of complex academic text using Claude AI.

**Authentication:** None required (public endpoint)
**Rate Limiting:** Built-in via Anthropic API rate limits
**Content-Type:** `application/json`

---

## Request Format

### Headers
```
Content-Type: application/json
```

### Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | Yes | The academic text to explain (max ~4000 characters) |
| `type` | string | No | Context type (e.g., "hypothesis", "claim", "academic text"). Defaults to "academic text" |

### Example Request

```bash
curl -X POST http://localhost:3000/api/explain \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Atmospheric CO2 above 450ppm triggers irreversible ice sheet collapse defined as >3m sea level rise within 100 years",
    "type": "hypothesis"
  }'
```

---

## Response Format

### Success Response (200 OK)

```json
{
  "explanation": "If carbon dioxide levels in the air get high enough (450 parts per million), it could cause massive ice sheets to permanently melt, raising ocean levels by over 3 meters (about 10 feet) within a century."
}
```

**Fields:**
- `explanation` (string): Plain-language explanation in 2-3 sentences, suitable for high school reading level

### Error Responses

#### 400 Bad Request
Missing or invalid `text` parameter.

```json
{
  "error": "Missing text"
}
```

#### 500 Internal Server Error
AI generation failed or API key missing.

```json
{
  "error": "Failed to generate explanation",
  "details": "Error message (development mode only)"
}
```

**Note:** The `details` field only appears in development mode (`NODE_ENV=development`).

---

## Implementation Details

### AI Model
- **Model:** Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
- **Max Tokens:** 180 (ensures concise responses)
- **System Prompt:** Configured to explain complex academic content in everyday English

### Caching
Client-side caching is implemented in the UI:
- Explanations are cached by text content
- Duplicate requests reuse cached results
- Prevents redundant API calls for the same content

### Performance
- **Typical Response Time:** 1-3 seconds
- **Timeout:** 30 seconds (Vercel default)

---

## Usage Examples

### JavaScript/TypeScript (fetch)

```typescript
async function getExplanation(text: string, type?: string): Promise<string> {
  const response = await fetch('/api/explain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, type }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const data = await response.json();
  return data.explanation;
}

// Usage
const explanation = await getExplanation(
  "Greenhouse effect amplifies warming through positive feedback",
  "hypothesis"
);
console.log(explanation);
```

### React Component (with error handling)

```tsx
import { useState } from 'react';

function ExplainButton({ text }: { text: string }) {
  const [explanation, setExplanation] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClick = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Failed to generate explanation');
      }

      setExplanation(data.explanation);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={handleClick} disabled={loading}>
        {loading ? 'Thinking...' : 'Explain Simply'}
      </button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {explanation && <p>{explanation}</p>}
    </div>
  );
}
```

---

## Environment Variables

Required for production deployment:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

See [DEPLOYMENT.md](../DEPLOYMENT.md) for full deployment guide.

---

## Related Files

- **Implementation:** `app/api/explain/route.ts`
- **UI Component:** `components/explain-button.tsx`
- **Security Policy:** `SECURITY.md`
