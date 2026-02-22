# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.x     | :white_check_mark: |
| < 2.0   | :x:                |

Only the latest version (main branch) receives security updates.

---

## Security Practices

### API Key Management

#### ✅ DO

- **Store keys in environment variables:**
  ```bash
  # .env (never commit this file)
  ANTHROPIC_API_KEY=sk-ant-api03-...
  ```

- **Use Vercel environment variables** for production:
  ```bash
  vercel env add ANTHROPIC_API_KEY
  ```

- **Rotate keys periodically** (every 90 days recommended)

- **Use separate keys** for development and production

#### ❌ DON'T

- **Never commit `.env` files** to git
  - Already in `.gitignore`, but verify: `git check-ignore .env`

- **Never hardcode API keys** in source code
  ```javascript
  // ❌ WRONG
  const apiKey = "sk-ant-api03-...";

  // ✅ CORRECT
  const apiKey = process.env.ANTHROPIC_API_KEY;
  ```

- **Never log API keys** in console output or error messages

- **Never share keys** in screenshots, issues, or pull requests

---

## Data Privacy

### No User Data Stored

- **Explanation requests are stateless** — no user input is stored in databases
- **Client-side caching only** — explanations cached in browser memory
- **No cookies or tracking** — application doesn't use cookies for tracking
- **No analytics by default** — no third-party analytics integrated

### API Request Flow

```
User → Frontend → /api/explain → Anthropic API → Response
                                      ↓
                          (Not stored anywhere)
```

**Data is never:**
- Saved to a database
- Logged to disk (except Vercel function logs, which expire)
- Shared with third parties (except Anthropic for processing)

### Anthropic Data Policy

Per [Anthropic's API policy](https://www.anthropic.com/legal/privacy):
- API requests **are not used** to train models
- Data **is not retained** beyond 30 days for trust & safety
- See their policy for full details

---

## Rate Limiting

### Built-in Protections

1. **Client-side deduplication:**
   - Duplicate requests cached and reused
   - Prevents redundant API calls

2. **Anthropic API rate limits:**
   - Automatically enforced by Anthropic
   - Tier-based limits (see Anthropic dashboard)

3. **Vercel Serverless limits:**
   - 10-second timeout (Hobby tier)
   - Prevents runaway requests

### Recommended Additional Protections

For production deployments with high traffic, consider:

```typescript
// middleware.ts (example - not included by default)
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, "1 m"), // 10 requests per minute
});

export async function middleware(request: Request) {
  const ip = request.headers.get("x-forwarded-for") ?? "127.0.0.1";
  const { success } = await ratelimit.limit(ip);

  if (!success) {
    return new Response("Rate limit exceeded", { status: 429 });
  }

  return NextResponse.next();
}
```

**Note:** This requires Upstash Redis (not included — add if needed).

---

## Dependency Security

### Automated Scanning

GitHub Dependabot is enabled for automatic vulnerability scanning:
- **Security alerts** — Auto-created when vulnerabilities detected
- **Automated PRs** — Dependabot creates PRs to update vulnerable packages

### Manual Audit

Run security audit regularly:

```bash
npm audit
npm audit fix  # Apply automatic fixes
```

For breaking changes:
```bash
npm audit fix --force  # Use with caution
```

### Keep Dependencies Updated

```bash
# Check for outdated packages
npm outdated

# Update non-breaking changes
npm update

# Update major versions (review changes first)
npm install <package>@latest
```

---

## Content Security Policy

### Current Headers

No custom CSP headers are configured. Next.js default security headers apply.

### Recommended Production CSP

Add to `next.config.js` if needed:

```javascript
const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-eval' 'unsafe-inline'", // Next.js requires unsafe-inline
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: https:",
      "font-src 'self'",
      "connect-src 'self' https://api.anthropic.com",
    ].join('; ')
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff'
  },
  {
    key: 'X-Frame-Options',
    value: 'DENY'
  },
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block'
  },
];

module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: securityHeaders,
      },
    ];
  },
};
```

---

## Reporting a Vulnerability

### How to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead:

1. **Email:** [security contact - add your email]
2. **Subject:** "Security Vulnerability in Atlantis"
3. **Include:**
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Initial response:** Within 48 hours
- **Status update:** Within 1 week
- **Fix timeline:** Depends on severity
  - **Critical:** Immediate (within 24-48 hours)
  - **High:** Within 1 week
  - **Medium:** Within 2 weeks
  - **Low:** Next release cycle

### Disclosure Policy

- **Coordinated disclosure** preferred
- Security fixes released before public disclosure
- Credit given to reporter (if desired)

---

## Security Checklist

Before deploying to production:

- [ ] `.env` file is in `.gitignore` and not committed
- [ ] API keys stored in Vercel environment variables
- [ ] No hardcoded credentials in source code
- [ ] `npm audit` shows no high/critical vulnerabilities
- [ ] All dependencies up to date
- [ ] HTTPS enabled (automatic with Vercel)
- [ ] No sensitive data logged in API routes

Optional but recommended:

- [ ] Custom domain configured with HTTPS
- [ ] Rate limiting configured (if high traffic expected)
- [ ] Security headers configured in next.config.js
- [ ] Error messages don't expose sensitive information
- [ ] API key rotation schedule established

---

## Additional Resources

- **OWASP Top 10:** [owasp.org/www-project-top-ten](https://owasp.org/www-project-top-ten/)
- **Next.js Security:** [nextjs.org/docs/app/building-your-application/configuring/environment-variables](https://nextjs.org/docs/app/building-your-application/configuring/environment-variables)
- **Vercel Security:** [vercel.com/docs/security](https://vercel.com/docs/security)
- **Anthropic Security:** [docs.anthropic.com/en/api/security](https://docs.anthropic.com/en/api/security)

---

## Version History

- **2.0.0** (Current): Initial security policy
  - Environment variable management
  - No data storage policy
  - Vulnerability reporting process
