#!/usr/bin/env python3
"""Demo script for the Asset Management System.

This script demonstrates the capabilities of the asset management system
including loading different asset types, caching, discovery, and resource
management.
"""

import os
import json
import tempfile
from pathlib import Path

from assets import (
    AssetManager, initialize_asset_manager,
    AssetType, SpriteAsset, FontAsset, ThemeAsset, DataAsset,
    CachePolicy, get_loader_registry
)


def create_demo_assets(demo_dir: Path) -> None:
    """Create demo assets for testing.
    
    Args:
        demo_dir (Path): Directory to create assets in
    """
    print(f"📁 Creating demo assets in {demo_dir}")
    
    # Create directory structure
    (demo_dir / "sprites").mkdir(exist_ok=True)
    (demo_dir / "fonts").mkdir(exist_ok=True)
    (demo_dir / "themes").mkdir(exist_ok=True)
    (demo_dir / "data").mkdir(exist_ok=True)
    (demo_dir / "sounds").mkdir(exist_ok=True)
    
    # Create sprite assets (mock PNG files)
    sprites = [
        "player.png", "enemy_orc.png", "enemy_troll.png",
        "potion_healing.png", "scroll_lightning.png", "sword.png"
    ]
    for sprite in sprites:
        (demo_dir / "sprites" / sprite).write_bytes(b'PNG_MOCK_DATA_' + sprite.encode())
    
    # Create font assets (mock TTF files)
    fonts = ["arial.ttf", "courier.ttf", "fantasy.ttf"]
    for font in fonts:
        (demo_dir / "fonts" / font).write_bytes(b'TTF_MOCK_DATA_' + font.encode())
    
    # Create sound assets (mock WAV files)
    sounds = ["attack.wav", "heal.wav", "death.wav", "pickup.wav"]
    for sound in sounds:
        (demo_dir / "sounds" / sound).write_bytes(b'WAV_MOCK_DATA_' + sound.encode())
    
    # Create theme assets
    themes = {
        "dark_theme.json": {
            "name": "Dark Theme",
            "version": "1.0",
            "colors": {
                "background": "#1a1a1a",
                "text": "#ffffff",
                "primary": "#4a9eff",
                "secondary": "#ff6b4a",
                "success": "#4aff6b",
                "warning": "#ffeb4a",
                "error": "#ff4a4a"
            },
            "fonts": {
                "default": "arial.ttf",
                "monospace": "courier.ttf",
                "title": "fantasy.ttf"
            },
            "styles": {
                "button": {
                    "padding": 8,
                    "border_width": 2,
                    "border_radius": 4
                },
                "panel": {
                    "padding": 12,
                    "border_width": 1
                }
            }
        },
        "light_theme.json": {
            "name": "Light Theme",
            "version": "1.0",
            "colors": {
                "background": "#ffffff",
                "text": "#333333",
                "primary": "#007acc",
                "secondary": "#cc7a00",
                "success": "#00cc7a",
                "warning": "#cccc00",
                "error": "#cc0000"
            },
            "fonts": {
                "default": "arial.ttf",
                "monospace": "courier.ttf"
            }
        }
    }
    
    for filename, theme_data in themes.items():
        with open(demo_dir / "themes" / filename, 'w') as f:
            json.dump(theme_data, f, indent=2)
    
    # Create game data assets
    game_data = {
        "monsters.json": {
            "version": "1.0",
            "monsters": [
                {
                    "name": "Orc",
                    "hp": 20,
                    "power": 4,
                    "defense": 0,
                    "sprite": "enemy_orc.png"
                },
                {
                    "name": "Troll",
                    "hp": 30,
                    "power": 8,
                    "defense": 2,
                    "sprite": "enemy_troll.png"
                }
            ]
        },
        "items.json": {
            "version": "1.0",
            "items": [
                {
                    "name": "Healing Potion",
                    "type": "consumable",
                    "effect": "heal",
                    "value": 40,
                    "sprite": "potion_healing.png"
                },
                {
                    "name": "Lightning Scroll",
                    "type": "consumable",
                    "effect": "lightning",
                    "damage": 20,
                    "sprite": "scroll_lightning.png"
                }
            ]
        },
        "config.json": {
            "version": "1.0",
            "game": {
                "title": "RLike Demo",
                "screen_width": 80,
                "screen_height": 50,
                "fps": 60
            },
            "player": {
                "starting_hp": 100,
                "starting_power": 5,
                "starting_defense": 1
            }
        }
    }
    
    for filename, data in game_data.items():
        with open(demo_dir / "data" / filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    print(f"✅ Created {len(sprites)} sprites, {len(fonts)} fonts, {len(sounds)} sounds")
    print(f"✅ Created {len(themes)} themes, {len(game_data)} data files")


def demo_basic_loading(manager: AssetManager) -> None:
    """Demonstrate basic asset loading.
    
    Args:
        manager (AssetManager): Asset manager instance
    """
    print("\n🔄 === Basic Asset Loading Demo ===")
    
    try:
        # Load different types of assets
        print("Loading sprite asset...")
        player_sprite = manager.load("sprites/player.png")
        print(f"✅ Loaded: {player_sprite.path} (Type: {player_sprite.asset_type.name})")
        
        print("Loading font asset...")
        font = manager.load("fonts/arial.ttf")
        print(f"✅ Loaded: {font.path} (Family: {font.family_name})")
        
        print("Loading theme asset...")
        theme = manager.load("themes/dark_theme.json")
        print(f"✅ Loaded: {theme.path} (Theme: {theme.theme_name})")
        print(f"   Colors: {list(theme.colors.keys())}")
        
        print("Loading data asset...")
        monsters = manager.load("data/monsters.json", asset_type=AssetType.DATA)
        print(f"✅ Loaded: {monsters.path} (Format: {monsters.format})")
        print(f"   Monster count: {len(monsters.data.get('monsters', []))}")
        
    except Exception as e:
        print(f"❌ Error loading assets: {e}")


def demo_aliases_and_caching(manager: AssetManager) -> None:
    """Demonstrate asset aliases and caching.
    
    Args:
        manager (AssetManager): Asset manager instance
    """
    print("\n🏷️  === Aliases and Caching Demo ===")
    
    # Add aliases for commonly used assets
    manager.add_alias("player", "sprites/player.png")
    manager.add_alias("orc", "sprites/enemy_orc.png")
    manager.add_alias("troll", "sprites/enemy_troll.png")
    manager.add_alias("dark_ui", "themes/dark_theme.json")
    
    print("Added aliases: player, orc, troll, dark_ui")
    
    # Load using aliases
    print("Loading assets using aliases...")
    player = manager.load("player")
    orc = manager.load("orc")
    theme = manager.load("dark_ui")
    
    print(f"✅ Player sprite loaded via alias: {player.path}")
    print(f"✅ Orc sprite loaded via alias: {orc.path}")
    print(f"✅ Dark theme loaded via alias: {theme.path}")
    
    # Show cache statistics
    stats = manager.get_cache_stats()
    print(f"\n📊 Cache Statistics:")
    print(f"   Hits: {stats.hits}, Misses: {stats.misses}")
    print(f"   Hit Rate: {stats.hit_rate:.1%}")
    print(f"   Memory Usage: {stats.memory_usage:,} bytes")
    print(f"   Cached Assets: {stats.asset_count}")
    
    # Demonstrate cache policies
    print("\n🔧 Setting cache policies...")
    manager.set_cache_policy("player", CachePolicy.ALWAYS)  # Keep player sprite always
    manager.set_cache_policy("orc", CachePolicy.LRU)        # Normal LRU for enemies
    print("✅ Set cache policies (player: ALWAYS, orc: LRU)")


def demo_asset_discovery(manager: AssetManager) -> None:
    """Demonstrate asset discovery and cataloging.
    
    Args:
        manager (AssetManager): Asset manager instance
    """
    print("\n🔍 === Asset Discovery Demo ===")
    
    # Discover all assets
    print("Scanning for assets...")
    result = manager.discover_assets(force_rescan=True)
    
    print(f"✅ Discovery completed in {result.scan_time:.2f}s")
    print(f"   Total files scanned: {result.total_files}")
    print(f"   Assets found: {result.assets_found}")
    
    # Show assets by type
    print("\n📋 Assets by type:")
    for asset_type, count in result.assets_by_type.items():
        print(f"   {asset_type.name}: {count}")
    
    # Get catalog and show some statistics
    catalog = manager.get_catalog()
    print(f"\n📚 Catalog Statistics:")
    print(f"   Total assets: {catalog.get_asset_count()}")
    print(f"   Total size: {catalog.get_total_size():,} bytes")
    
    # Find assets by criteria
    print("\n🔎 Finding assets by criteria:")
    
    # Find all sprites
    sprites = manager.find_assets(asset_type=AssetType.SPRITE)
    print(f"   Sprites found: {len(sprites)}")
    for sprite in sprites[:3]:  # Show first 3
        print(f"     - {Path(sprite.path).name}")
    
    # Find assets with "enemy" in name
    enemies = manager.find_assets(query="enemy")
    print(f"   Assets with 'enemy' in name: {len(enemies)}")
    for enemy in enemies:
        print(f"     - {Path(enemy.path).name}")
    
    # Find theme assets
    themes = manager.find_assets(asset_type=AssetType.THEME)
    print(f"   Themes found: {len(themes)}")
    for theme in themes:
        print(f"     - {Path(theme.path).name}")


def demo_loader_registry() -> None:
    """Demonstrate loader registry functionality."""
    print("\n⚙️  === Loader Registry Demo ===")
    
    registry = get_loader_registry()
    
    # Show supported extensions
    print("Supported file extensions:")
    extensions = registry.get_supported_extensions()
    for ext in sorted(extensions):
        asset_type = registry.detect_asset_type(f"test{ext}")
        print(f"   {ext} -> {asset_type.name if asset_type else 'Unknown'}")
    
    # Show loaders by type
    print("\nLoaders by asset type:")
    for asset_type in AssetType:
        loaders = registry.get_loaders_for_type(asset_type)
        if loaders:
            print(f"   {asset_type.name}: {len(loaders)} loader(s)")
            for loader in loaders:
                print(f"     - {loader.__class__.__name__}: {loader.supported_extensions}")


def demo_memory_management(manager: AssetManager) -> None:
    """Demonstrate memory management features.
    
    Args:
        manager (AssetManager): Asset manager instance
    """
    print("\n💾 === Memory Management Demo ===")
    
    # Load several assets to show memory usage
    assets_to_load = [
        "sprites/player.png",
        "sprites/enemy_orc.png", 
        "sprites/enemy_troll.png",
        "fonts/arial.ttf",
        "themes/dark_theme.json",
        "data/monsters.json"
    ]
    
    print("Loading multiple assets...")
    for asset_path in assets_to_load:
        try:
            asset = manager.load(asset_path)
            print(f"   ✅ {Path(asset_path).name}")
        except Exception as e:
            print(f"   ❌ {Path(asset_path).name}: {e}")
    
    # Show memory usage
    memory_usage = manager.get_memory_usage()
    asset_count = manager.get_loaded_asset_count()
    
    print(f"\n📊 Memory Usage:")
    print(f"   Loaded assets: {asset_count}")
    print(f"   Memory usage: {memory_usage:,} bytes ({memory_usage / 1024:.1f} KB)")
    
    # Demonstrate unloading
    print("\n🗑️  Unloading some assets...")
    unloaded = manager.unload("sprites/enemy_troll.png")
    print(f"   Troll sprite unloaded: {unloaded}")
    
    # Show updated stats
    new_memory = manager.get_memory_usage()
    new_count = manager.get_loaded_asset_count()
    print(f"   Updated - Assets: {new_count}, Memory: {new_memory:,} bytes")
    
    # Clear cache
    print("\n🧹 Clearing entire cache...")
    manager.clear_cache()
    final_memory = manager.get_memory_usage()
    final_count = manager.get_loaded_asset_count()
    print(f"   Final - Assets: {final_count}, Memory: {final_memory:,} bytes")


def main():
    """Main demo function."""
    print("🎮 Asset Management System Demo")
    print("=" * 50)
    
    # Create temporary directory for demo assets
    with tempfile.TemporaryDirectory() as temp_dir:
        demo_dir = Path(temp_dir)
        
        # Create demo assets
        create_demo_assets(demo_dir)
        
        # Initialize asset manager
        print(f"\n🚀 Initializing Asset Manager...")
        manager = initialize_asset_manager(
            asset_paths=[str(demo_dir)],
            cache_size=10 * 1024 * 1024,  # 10MB cache
            max_cached_assets=100,
            enable_hot_reload=True,
            auto_discover=False  # We'll do manual discovery for demo
        )
        print("✅ Asset Manager initialized")
        
        # Run demos
        demo_basic_loading(manager)
        demo_aliases_and_caching(manager)
        demo_asset_discovery(manager)
        demo_loader_registry()
        demo_memory_management(manager)
        
        print("\n🎉 Demo completed successfully!")
        print("\nThe Asset Management System provides:")
        print("  ✅ Unified loading of multiple asset types")
        print("  ✅ Intelligent caching with configurable policies")
        print("  ✅ Automatic asset discovery and cataloging")
        print("  ✅ Flexible loader system with format detection")
        print("  ✅ Memory management and hot-reloading")
        print("  ✅ Asset aliases and dependency tracking")
        print("  ✅ Comprehensive error handling and validation")


if __name__ == "__main__":
    main()
