# Deployment Guide

Complete guide for deploying Atlantis to Vercel.

---

## Prerequisites

- **Node.js:** 20.x (specified in `.nvmrc`)
- **npm:** Latest version
- **Vercel Account:** Free tier works for most use cases
- **Anthropic API Key:** Required for `/api/explain` endpoint

---

## Quick Start

### 1. Install Vercel CLI

```bash
npm install -g vercel
```

### 2. Login to Vercel

```bash
vercel login
```

### 3. Set Environment Variables

```bash
vercel env add ANTHROPIC_API_KEY
```

When prompted, paste your API key and select all environments (Production, Preview, Development).

### 4. Deploy

```bash
vercel --prod
```

Your site will be live at `https://your-project.vercel.app`

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key for explanation generation | `sk-ant-api03-...` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `NODE_ENV` | Environment mode | `production` |

**Important:** Never commit `.env` files to git. The `.env` file is already in `.gitignore`.

---

## Vercel Configuration

### Build Settings

The project uses default Next.js 15 build settings:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm install",
  "framework": "nextjs"
}
```

**No custom configuration needed** — Vercel auto-detects Next.js projects.

### Node Version

Vercel will use Node.js 20.x as specified in `.nvmrc`:

```
20
```

### TypeScript Configuration

The project uses strict TypeScript with ES2022 target:
- `target`: ES2022
- `strict`: true
- `moduleResolution`: bundler

See `tsconfig.json` for full configuration.

---

## Auto-Deploy from Git

### GitHub Integration (Recommended)

1. **Connect Repository:**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Select your GitHub repository
   - Click "Import"

2. **Configure Project:**
   - Framework preset: Next.js
   - Root directory: `./`
   - Build command: (leave default)
   - Output directory: (leave default)

3. **Add Environment Variables:**
   - Add `ANTHROPIC_API_KEY` in project settings

4. **Deploy:**
   - Click "Deploy"
   - Future `git push` to `main` branch auto-deploys

### Branch Deployments

- **Production:** `main` branch → `your-project.vercel.app`
- **Preview:** All other branches → `your-project-git-branch.vercel.app`
- **Pull Requests:** Automatic preview deployments with unique URLs

---

## Custom Domain Setup

### Add Custom Domain

1. Go to Project Settings → Domains
2. Add your domain (e.g., `atlantis.example.com`)
3. Configure DNS with your registrar:

**Option A: CNAME Record (Recommended)**
```
Type: CNAME
Name: atlantis (or @)
Value: cname.vercel-dns.com
```

**Option B: A Record**
```
Type: A
Name: @ (or subdomain)
Value: 76.76.21.21
```

4. Vercel automatically provisions SSL certificate (Let's Encrypt)

### Domain Verification

Vercel will provide TXT record for verification:
```
Type: TXT
Name: _vercel
Value: [verification code from Vercel]
```

Add this to your DNS, then click "Verify" in Vercel dashboard.

---

## Performance Optimization

### Automatic Optimizations (Built-in)

- ✅ **Image Optimization:** Next.js Image component auto-optimizes
- ✅ **Static Generation:** Pages pre-rendered at build time
- ✅ **Edge Caching:** Static assets cached on Vercel Edge Network
- ✅ **Compression:** Automatic gzip/brotli compression

### Bundle Size

Check production bundle size:
```bash
npm run build
```

Look for build output showing page sizes. All pages should be under 200KB.

### API Routes

API routes (`/api/explain`) run on Vercel Serverless Functions:
- **Cold Start:** ~500ms first request
- **Warm Response:** <100ms subsequent requests
- **Timeout:** 10s (Hobby), 60s (Pro)

---

## Monitoring & Debugging

### View Logs

```bash
vercel logs [deployment-url]
```

Or view in Vercel Dashboard → Deployments → [deployment] → Logs

### Common Issues

#### Build Fails with TypeScript Errors

```bash
# Check locally first
npx tsc --noEmit
npm run build
```

Fix all TypeScript errors before deploying.

#### API Key Not Working

Verify environment variable is set:
```bash
vercel env ls
```

If missing, add it:
```bash
vercel env add ANTHROPIC_API_KEY
```

Then redeploy:
```bash
vercel --prod
```

#### 404 on Dynamic Routes

Ensure `output: 'export'` is NOT in `next.config.js` (it disables API routes).

---

## Rollback

### Revert to Previous Deployment

1. Go to Vercel Dashboard → Deployments
2. Find the working deployment
3. Click "⋯" → Promote to Production

Or via CLI:
```bash
vercel rollback
```

---

## CI/CD Pipeline (GitHub Actions)

Optional: Add automated checks before Vercel deployment.

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run build
      - run: npx tsc --noEmit
```

This runs type-checking and builds on every push, catching errors before Vercel deployment.

---

## Cost Estimation

### Vercel Hobby (Free Tier)

- ✅ Unlimited deployments
- ✅ 100 GB bandwidth/month
- ✅ Serverless functions included
- ✅ Automatic HTTPS

**Sufficient for:** Personal projects, demos, low-traffic sites

### Vercel Pro ($20/month)

- Increased bandwidth (1 TB/month)
- Longer function execution time (60s vs 10s)
- Password protection
- Analytics

**Needed for:** Production sites with significant traffic

### Anthropic API Costs

Separate from Vercel hosting:
- **Claude Sonnet 4:** $3/million input tokens, $15/million output tokens
- **Typical explanation:** ~100 input + 50 output tokens ≈ $0.0011/request
- **1000 explanations/month:** ~$1.10

---

## Support

- **Vercel Docs:** [vercel.com/docs](https://vercel.com/docs)
- **Next.js Docs:** [nextjs.org/docs](https://nextjs.org/docs)
- **Anthropic API:** [docs.anthropic.com](https://docs.anthropic.com)
- **Project Issues:** [github.com/teddygcodes/atlantis/issues](https://github.com/teddygcodes/atlantis/issues)

---

## Security

See [SECURITY.md](./SECURITY.md) for security best practices and vulnerability reporting.
