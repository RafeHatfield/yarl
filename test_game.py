#!/usr/bin/env python3
"""
Convenience script to run Yarl in testing mode.

This script automatically enables testing mode with increased item spawn rates,
making it easier to test scrolls, equipment, and other game mechanics.
"""

import subprocess
import sys
import os

def main():
    """Run the game in testing mode."""
    print("🧪 Starting Yarl in TESTING MODE...")
    print("   - Increased item spawn rates (10-20 items per room)")
    print("   - All scrolls and equipment available from level 1")
    print("   - Perfect for testing game mechanics!")
    print()
    
    # Change to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    try:
        # Run the game with testing flag
        subprocess.run([sys.executable, "engine.py", "--testing"], check=True)
    except KeyboardInterrupt:
        print("\n🎮 Game stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running game: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
