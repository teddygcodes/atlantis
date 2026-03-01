#!/bin/bash
# Mock smoke test with real Claude API calls
# This tests the full end-to-end system at reduced scale

echo "======================================================================"
echo "  ATLANTIS MOCK SMOKE TEST"
echo "======================================================================"
echo ""
echo "This will run a quick end-to-end test with REAL Claude API calls."
echo ""
echo "Settings for this mock run:"
echo "  - Founding research: 3 cycles (not 10)"
echo "  - Convention: 4 full debate rounds (unchanged)"
echo "  - Founding Era: form 3 States (not 20)"
echo "  - Governance: 5 cycles (not 10)"
echo ""
echo "Expected cost: ~$2-5 (using Claude Sonnet 4.5)"
echo ""
echo "======================================================================"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "ERROR: .env file not found"
    echo ""
    echo "Please create a .env file with your API key:"
    echo ""
    echo "  1. Copy the example: cp .env.example .env"
    echo "  2. Edit .env and add your API key"
    echo "  3. Get your key from: https://console.anthropic.com/settings/keys"
    echo ""
    exit 1
fi

# Check if API key is set in .env
if ! grep -q "ANTHROPIC_API_KEY=sk-" .env 2>/dev/null; then
    echo "WARNING: API key may not be set in .env file"
    echo ""
    echo "Please edit .env and add your API key:"
    echo "  ANTHROPIC_API_KEY=sk-ant-xxxxx"
    echo ""
    echo "Get your key from: https://console.anthropic.com/settings/keys"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Clean up previous mock data
echo "Cleaning previous mock data..."
rm -rf atlantis_mock atlantis_data

# Run the mock test
echo ""
echo "Starting mock test..."
echo ""

python3 -u __main__.py --mock 2>&1 | tee /tmp/mock_output.log

# Show the results
echo ""
echo "======================================================================"
echo "  MOCK TEST COMPLETE"
echo "======================================================================"
echo ""
echo "Mock data saved to: atlantis_mock/"
echo ""
