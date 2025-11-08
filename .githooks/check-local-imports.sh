#!/bin/bash
# Pre-commit hook: Prevent local imports that cause scoping bugs
# 
# Problem: Local imports (imports inside functions) cause Python scoping bugs
# where the local import shadows module-level references, breaking other code.
# Example: Importing ComponentType inside a function caused 6-commit debugging cycles.
#
# Solution: This hook detects staged files with local imports and prevents commit.
#
# Install: git config core.hooksPath .githooks
# Make executable: chmod +x .githooks/check-local-imports.sh

echo "🔍 Checking for local imports..."

# Get list of staged Python files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep "\.py$")

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

# Check for local imports (indented from...import statements, excluding TYPE_CHECKING)
VIOLATIONS=$(echo "$STAGED_FILES" | xargs grep -l "^    from.*import" 2>/dev/null | \
    xargs grep "^    from.*import" 2>/dev/null | \
    grep -v "TYPE_CHECKING" | \
    grep -v "\.direnv" | \
    grep -v "source/")

if [ -n "$VIOLATIONS" ]; then
    echo ""
    echo "❌ ERROR: Local imports detected in staged files!"
    echo ""
    echo "The following lines have imports inside functions:"
    echo "$VIOLATIONS"
    echo ""
    echo "🔧 How to fix:"
    echo "   1. Move ALL 'from ... import' statements to the TOP of the file"
    echo "   2. They must have NO indentation (column 0)"
    echo ""
    echo "❌ WRONG:"
    echo "    def some_function():"
    echo "        from components.fighter import Fighter"
    echo ""
    echo "✅ CORRECT:"
    echo "    from components.fighter import Fighter"
    echo ""
    echo "    def some_function():"
    echo "        fighter = Fighter(...)"
    echo ""
    echo "⚠️  Why this matters:"
    echo "    Local imports shadow module-level references in Python's scoping rules."
    echo "    This causes silent bugs that hide for months (like ComponentType bug)."
    echo "    Pre-commit hook prevents this class of bugs entirely."
    echo ""
    exit 1
fi

echo "✅ No local imports found"
exit 0

