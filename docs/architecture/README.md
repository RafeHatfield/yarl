# Architecture Documentation

This folder contains documentation about Yarl's core architectural systems and design patterns.

## Contents

### Portal System
- **[portal_system.md](portal_system.md)** - Complete specification for the portal system including Phase A (core mechanics) and Phase B (monster AI integration, visual feedback)

### Session Handoff Template
- **[session_handoff_template.md](session_handoff_template.md)** - Template for passing context between development sessions

## Key Systems

- **Entity Component System (ECS)** - Core architecture for game objects
- **AI System** - Monster behavior and pathfinding
- **Rendering Pipeline** - Viewport-based rendering with FOV
- **Portal System** - Two-dimensional teleportation with monster interaction

## Design Principles

See [DESIGN_PRINCIPLES.md](../../DESIGN_PRINCIPLES.md) in root for core architectural philosophy.

## Adding to This Documentation

When adding architectural documentation:
1. Focus on system design, not implementation details
2. Include use cases and design tradeoffs
3. Link to relevant code files
4. Explain integration points with other systems

