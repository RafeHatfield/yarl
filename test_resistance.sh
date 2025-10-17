#!/bin/bash
# Quick test script for Resistance System v3.12.0

echo "=============================================="
echo "🛡️  RESISTANCE SYSTEM TEST MODE"
echo "=============================================="
echo ""
echo "This will launch the game with:"
echo "  - Resistance logging enabled (watch console)"
echo "  - Boss monsters have resistances:"
echo "    • Dragon Lord: 100% fire, 50% cold, 30% poison"
echo "    • Demon King: 75% fire, 100% poison, 50% lightning"
echo ""
echo "Testing tips:"
echo "  1. Go to Level 8 to fight bosses"
echo "  2. Use different elemental scrolls:"
echo "     - Fireball (fire damage)"
echo "     - Lightning Bolt (lightning damage)"
echo "     - Dragon Fart (poison damage)"
echo "  3. Watch the console for resistance messages"
echo "  4. Check in-game messages for immunity/resistance"
echo ""
echo "See TESTING_RESISTANCE_SYSTEM.md for detailed guide"
echo "=============================================="
echo ""
read -p "Press Enter to start the game..."

# Set testing mode flag (optional, for additional debug features)
export YARL_TESTING_MODE=1

# Run the game
python3 engine.py

# Note: Resistance logging is always active now,
# so you'll see messages even without testing mode

