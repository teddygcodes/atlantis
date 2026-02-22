# Running Atlantis

## Prerequisites

### Required Software
- **Python 3.11+** (tested on 3.11.7)
- **Node.js 20+** (for Next.js frontend)
- **npm** (package manager - standardized, no yarn/pnpm)
- **Git** (for cloning and version control)

### Required API Keys
- **Anthropic API Key** (Claude 4.5 family access)
  - Get from: https://console.anthropic.com/settings/keys
  - Store in `.env` file (see setup below)

### System Requirements
- **RAM:** 4GB minimum, 8GB recommended (for large archive processing)
- **Disk:** 1GB free space (for output/ directory and node_modules/)
- **Network:** Stable internet connection (API calls, npm installs)

---

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/atlantis.git
cd atlantis
```

### 2. Backend Setup (Python)
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "from core.engine import AtlantisEngine; print('✓ Backend ready')"
```

### 3. Frontend Setup (Next.js)
```bash
# Install Node dependencies
npm install

# Verify build
npm run build
```

### 4. Environment Configuration
Create `.env` file in project root:
```bash
# Copy example template
cp .env.example .env

# Edit with your API key
nano .env
```

Add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
```

**Security:** `.env` is in `.gitignore` - never commit API keys to git.

---

## Running the Engine

### Quick Start (10-Domain Demo)
```bash
# Run with all 10 research domains (recommended first run)
python3 __main__.py --demo-10-domains
```

Expected output:
```
============================================================
  ATLANTIS V2.2
  The Lost Civilization, Rebuilt — Adversarial Knowledge Engine
============================================================

  [Phase 0] Founder Research — Free-Form Deposits
  Phase 0 complete. 20 Founder profiles archived.

  [Phase 1] Founding Era — Rival Pair Formation
  DEMO PAIR FORMED: Mathematics_Alpha vs Mathematics_Beta in 'Mathematics'
  ... (10 pairs total)
  Phase 1 complete. 10 rival pairs formed.

  [Phase 2] Autonomous Governance
  Cycle 1/3
  Processing 10 rival pairs...
```

### Command-Line Options

#### Mode Flags
```bash
# 10-domain demo (STEM + social sciences + humanities)
python3 __main__.py --demo-10-domains

# Electrical engineering demo (2 domains)
python3 __main__.py --demo-electrical

# Mock mode (fast, low-cost testing)
python3 __main__.py --mock

# Default mode (dynamic Founder voting, slower)
python3 __main__.py
```

#### Utility Flags
```bash
# Force clean start (delete previous run data)
python3 __main__.py --demo-10-domains --force-clean

# Dry run (show what would happen, no API calls)
python3 __main__.py --dry-run

# Verbose logging
python3 __main__.py --demo-10-domains --verbose
```

#### Combined Example
```bash
# Common dev workflow: fresh 10-domain run with verbose logs
python3 __main__.py --demo-10-domains --force-clean --verbose
```

---

## Data Pipeline: Engine → Frontend

### Step 1: Run Engine (Governance Cycles)
```bash
python3 __main__.py --demo-10-domains
```

**Outputs:**
- `output/atlantis.db` - SQLite database with full archive
- `output/logs/cycle_N.md` - Human-readable cycle logs
- `output/domain_health.json` - DMI metrics per domain
- `output/cost_summary.json` - API cost tracking

### Step 2: Generate Site Data
```bash
python3 generate_site_data.py
```

**What it does:**
- Reads `output/atlantis.db`
- Extracts archive entries, states, debates, domain pairs
- Exports TypeScript file: `lib/data.ts`

**Outputs:**
```typescript
// lib/data.ts
export const HYPOTHESES: Hypothesis[] = [...];
export const DEBATES: Debate[] = [...];
export const STATES: StateEntity[] = [...];
export const DOMAIN_PAIRS: DomainPair[] = [...];
```

### Step 3: Run Frontend (Next.js)
```bash
# Development server
npm run dev
# Visit: http://localhost:3000

# Production build
npm run build
npm start
```

### Step 4: Deploy to Vercel
```bash
# First time setup
npm install -g vercel
vercel login

# Deploy
vercel --prod
```

**Note:** Vercel reads `lib/data.ts` at build time - regenerate before deploying.

---

## Troubleshooting

### Engine Issues

#### Problem: `KeyError: 'model'` on startup
```
KeyError: 'model'
  File "core/llm.py", line 147, in complete
    model = model or API_CONFIG["model"]
```

**Fix:** Missing API_CONFIG keys in `config/settings.py`. Verify:
```python
API_CONFIG = {
    "model": "claude-sonnet-4-5-20250929",  # ADD THIS
    "max_tokens": 4096,                      # ADD THIS
    "temperature": 0.7,                      # ADD THIS
    "rate_limit_seconds": 0.1,
    ...
}
```

#### Problem: `ANTHROPIC_API_KEY not found`
**Fix:**
1. Check `.env` file exists in project root
2. Verify key format: `ANTHROPIC_API_KEY=sk-ant-api03-...`
3. No quotes needed around key
4. Restart terminal to reload environment

#### Problem: Claims rejected for "missing operational definition"
```
[validate_claim] Discovery claims should include POSITION or HYPOTHESIS with operational definition
```

**Fix:** HYPOTHESIS format requires explicit operational definition:
```
HYPOTHESIS: [testable prediction]
OPERATIONAL DEF: [key terms defined measurably]
STEP 1: [evidence]
CONCLUSION: [summary]
```

#### Problem: Cost tracking shows $0.00
**Fix:** Model ID mismatch in `core/llm.py:cost_rates`. Verify:
```python
self.cost_rates = {
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},  # Match actual ID
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
}
```

#### Problem: Run takes >1 hour
**Cause:** Using default mode (dynamic Founder voting) instead of demo mode.
**Fix:** Use `--demo-10-domains` or `--mock` for faster execution.

### Frontend Issues

#### Problem: `npm run build` fails with TypeScript errors
```
Type 'string | undefined' is not assignable to type 'string'
```

**Fix:** Missing null checks. Common in:
- `components/state-profile.tsx:304` - Empty stateHypotheses array
- `lib/data.ts` - Missing field exports from generate_site_data.py

**Resolution:**
```bash
# Regenerate data file
python3 generate_site_data.py

# Rebuild
npm run build
```

#### Problem: Archive page shows 0 claims
**Cause:** Filter excluding "SURVIVED" ruling type.
**Fix:** Check `components/archive.tsx:40`:
```typescript
const validatedHypotheses = HYPOTHESES.filter(
  (c) => c.ruling === "SURVIVED" || c.ruling === "REVISE" || c.ruling === "PARTIAL"
);
```

#### Problem: States page shows only 6 states instead of 20
**Cause:** `generate_site_data.py` not building domain pairs dynamically.
**Fix:** Verify `_build_domain_pairs()` function exists and:
```python
# Export domain pairs
domain_pairs = _build_domain_pairs(states)
```

### Database Issues

#### Problem: `database is locked`
**Cause:** Multiple processes accessing `output/atlantis.db`.
**Fix:**
```bash
# Check for running processes
ps aux | grep python

# Kill if stuck
pkill -f __main__.py

# Restart engine
python3 __main__.py --demo-10-domains
```

#### Problem: Archive has duplicate display_ids
**Cause:** `--force-clean` not used, mixing runs.
**Fix:**
```bash
# Always use --force-clean for fresh runs
rm -rf output/
python3 __main__.py --demo-10-domains --force-clean
```

---

## Performance Tips

### Speed Up Development Cycles

1. **Use Mock Mode for Testing**
   ```bash
   python3 __main__.py --mock  # No API calls, instant
   ```

2. **Reduce Governance Cycles**
   ```python
   # config/settings.py
   DEMO_10_DOMAINS_CONFIG = {
       "governance_cycles": 1,  # Was 3
   }
   ```

3. **Use Haiku for Everything (Cost Optimization)**
   ```python
   # config/settings.py
   MODEL_ALLOCATION = {
       "researcher_claims": "haiku",  # Was sonnet
       "judge": "haiku",               # Was sonnet
   }
   ```

### Optimize Frontend Build

1. **Disable Unused Pages**
   ```bash
   # Temporarily rename folders to exclude from build
   mv app/chronicle app/_chronicle
   npm run build  # Faster
   ```

2. **Use Dev Server (Hot Reload)**
   ```bash
   npm run dev  # No build step
   ```

---

## Development Workflow

### Typical Iteration Loop

```bash
# 1. Make code changes (e.g., fix researcher prompt)
nano governance/states.py

# 2. Run engine with fresh data
python3 __main__.py --demo-10-domains --force-clean

# 3. Check output
cat output/logs/cycle_1.md
sqlite3 output/atlantis.db "SELECT COUNT(*) FROM archive_entries;"

# 4. Generate frontend data
python3 generate_site_data.py

# 5. Test frontend
npm run dev
# Visit http://localhost:3000

# 6. Commit changes
git add .
git commit -m "fix: researcher prompt max_tokens"
git push
```

### Testing Before Production

```bash
# Backend validation
python3 -c "from core.engine import AtlantisEngine; print('✓ Imports work')"

# Frontend validation
npm run build  # Must succeed
npm run lint   # Must pass

# Full integration test
python3 __main__.py --demo-10-domains --force-clean
python3 generate_site_data.py
npm run build
npm start
# Verify http://localhost:3000 works
```

---

## Logs and Debugging

### Important Log Files
- `output/logs/cycle_N.md` - Full exchange records per cycle
- `output/logs/api_errors.log` - LLM API failures
- `output/cost_summary.json` - Cost tracking breakdown
- `output/domain_health.json` - DMI metrics evolution

### Enable Verbose Logging
```bash
python3 __main__.py --demo-10-domains --verbose
```

**Shows:**
- LLM prompt/response pairs
- Validation failures with reasons
- Token budget changes
- Domain health calculations

### Database Queries (Debugging)
```bash
sqlite3 output/atlantis.db

# Check claim counts by status
SELECT status, COUNT(*) FROM archive_entries GROUP BY status;

# Find destroyed claims with reasons
SELECT display_id, outcome_reasoning FROM archive_entries WHERE status='destroyed' LIMIT 5;

# Check State budgets
SELECT state_name, token_budget, tier FROM state_budgets;

# View validation failures
SELECT display_id, validation_json FROM archive_entries WHERE validation_json IS NOT NULL;
```

---

## Next Steps

After successful run:
1. Explore **[Knowledge Tiers](Knowledge-Tiers.md)** - Understand State progression
2. Read **[Token Economy](Token-Economy.md)** - Learn budget mechanics
3. Check **[Model Routing](Model-Routing.md)** - Optimize API costs
4. Review **[Roadmap](Roadmap.md)** - See what's coming in v2.3

For questions or issues: https://github.com/yourusername/atlantis/issues
