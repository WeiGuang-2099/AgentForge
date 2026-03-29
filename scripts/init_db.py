"""Database initialization script."""
import asyncio
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import yaml
from sqlalchemy import select

from app.models import Base, AgentConfig, init_db, AsyncSessionLocal
from app.models.database import engine


async def load_presets() -> None:
    """Load preset agent configurations from YAML files."""
    presets_dir = Path(__file__).parent.parent / "presets"
    
    if not presets_dir.exists():
        print(f"Presets directory not found: {presets_dir}")
        return
    
    async with AsyncSessionLocal() as session:
        # Load individual preset files
        for yaml_file in presets_dir.glob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    
                # Skip empty or comment-only files
                if not content or content.startswith("#"):
                    lines = content.split("\n")
                    # Check if file has actual content beyond comments
                    has_content = any(
                        line.strip() and not line.strip().startswith("#")
                        for line in lines
                    )
                    if not has_content:
                        print(f"Skipping empty preset file: {yaml_file.name}")
                        continue
                
                with open(yaml_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                
                if config is None:
                    print(f"Skipping empty preset file: {yaml_file.name}")
                    continue
                
                name = yaml_file.stem
                
                # Check if preset already exists
                result = await session.execute(
                    select(AgentConfig).where(AgentConfig.name == name)
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    print(f"Preset '{name}' already exists, skipping...")
                    continue
                
                # Create new preset
                agent_config = AgentConfig(
                    name=name,
                    display_name=config.get("display_name", name.title()),
                    description=config.get("description", ""),
                    model=config.get("model"),
                    system_prompt=config.get("system_prompt"),
                    tools=config.get("tools", []),
                    memory=config.get("memory"),
                    parameters=config.get("parameters"),
                    is_preset=True
                )
                session.add(agent_config)
                print(f"Loaded preset: {name}")
                
            except yaml.YAMLError as e:
                print(f"Error parsing {yaml_file.name}: {e}")
            except Exception as e:
                print(f"Error loading {yaml_file.name}: {e}")
        
        await session.commit()


async def main() -> None:
    """Initialize the database and load presets."""
    print("=" * 50)
    print("AgentForge Database Initialization")
    print("=" * 50)
    
    # Create all tables
    print("\n[1/2] Creating database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✓ Database tables created successfully!")
    except Exception as e:
        print(f"✗ Failed to create tables: {e}")
        raise
    
    # Load presets
    print("\n[2/2] Loading preset configurations...")
    try:
        await load_presets()
        print("✓ Preset configurations loaded!")
    except Exception as e:
        print(f"✗ Failed to load presets: {e}")
        raise
    
    print("\n" + "=" * 50)
    print("Database initialization completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
