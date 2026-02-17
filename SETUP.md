# Atlantis Setup Guide

## Quick Start (3 steps)

### 1. Add your API key to the `.env` file

Open the `.env` file and add your Anthropic API key:

```bash
# Edit the .env file
nano .env
```

Add your key:
```
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

**Get your API key**: https://console.anthropic.com/settings/keys

### 2. Install dependencies (if needed)

```bash
pip3 install -r requirements.txt
```

### 3. Run the mock test

```bash
./run_mock.sh
```

That's it! The mock test will run a quick end-to-end smoke test with real Claude API calls.

---

## What the Mock Test Does

The mock test runs the **full Atlantis system** at reduced scale:

- ✅ **Phase 0**: 3 research cycles (Founders building knowledge)
- ✅ **Phase 1**: 4 Convention rounds (real 2v2 adversarial debates)
- ✅ **Phase 2**: Government deployment
- ✅ **Phase 2.5**: Founding Era (Founders + permanent senators form 3 States)
- ✅ **Phase 3**: Founders retire, 5 governance cycles with State Senators

**Expected cost**: ~$2-5 for the full mock run
**Time**: ~5-10 minutes

---

## Command Options

```bash
# Mock test (recommended first run)
python3 __main__.py --mock

# Local simulation (no API calls, uses mock LLM)
python3 __main__.py --local --cycles 30

# Full production run (after mock succeeds)
python3 __main__.py --cycles 30
```

---

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
- Make sure you edited `.env` and added your API key
- The key should start with `sk-ant-`

### "Module not found: dotenv"
```bash
pip3 install python-dotenv
```

### "Module not found: anthropic"
```bash
pip3 install -r requirements.txt
```

---

## Next Steps

After the mock test succeeds:
1. Review the outputs (Convention debates, State formations, etc.)
2. Check token costs in the final status report
3. Run the full simulation: `python3 __main__.py --cycles 30`
