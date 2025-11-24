# ey-ay/scripts/migrate_json_to_db.py

import json
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

os.chdir(project_root)

try:
    from config.settings import AppConfig
    from config.logging_config import get_logger
    from database.operations import create_intent, add_pattern, add_response
except ImportError as e:
    print(f"\n✗ Import Error: {e}")
    print(f"Project root: {project_root}")
    print(f"Current dir: {os.getcwd()}")
    print("\nTrying alternative import method...")

    # Alternative: direct imports without config
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Import operations directly
    sys.path.insert(0, str(project_root / "database"))
    from database.operations import create_intent, add_pattern, add_response

    class AppConfig:
        DATA_DIR = project_root / "data"

else:
    logger = get_logger(__name__)

logger = get_logger(__name__)


def load_json_intents(json_path: str) -> dict:
    """Load intents from JSON file"""
    json_path = Path(json_path)

    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def migrate_intents(json_path: str, clear_existing: bool = False):
    logger.info("=" * 60)
    logger.info("Starting migration: JSON → MySQL")
    logger.info("=" * 60)

    # Load JSON data
    logger.info(f"Loading data from: {json_path}")
    data = load_json_intents(json_path)
    intents = data.get("intents", [])
    logger.info(f"Found {len(intents)} intents to migrate")

    # Clear existing data if requested
    if clear_existing:
        logger.warning("Clearing existing data...")
        from database.connection import get_db

        db = get_db()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            cursor.execute("TRUNCATE TABLE conversations")
            cursor.execute("TRUNCATE TABLE responses")
            cursor.execute("TRUNCATE TABLE patterns")
            cursor.execute("TRUNCATE TABLE intents")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            cursor.close()
        logger.info("✓ Existing data cleared")

    # Migrate each intent
    stats = {"intents": 0, "patterns": 0, "responses": 0, "errors": 0}

    for intent in intents:
        try:
            tag = intent["tag"]
            description = intent.get("description", "")

            logger.info(f"\nMigrating intent: {tag}")

            # Create intent
            try:
                intent_id = create_intent(tag, description)
                stats["intents"] += 1
                logger.info(f"  ✓ Created intent (ID: {intent_id})")
            except Exception as e:
                # Intent might already exist
                if "Duplicate entry" in str(e):
                    logger.warning(f"  ⚠ Intent '{tag}' already exists, skipping...")
                    continue
                else:
                    raise

            # Add patterns
            patterns = intent.get("patterns", [])
            for pattern in patterns:
                add_pattern(tag, pattern)
                stats["patterns"] += 1
            logger.info(f"  ✓ Added {len(patterns)} patterns")

            # Add responses
            responses = intent.get("responses", [])
            for response in responses:
                add_response(tag, response)
                stats["responses"] += 1
            logger.info(f"  ✓ Added {len(responses)} responses")

        except Exception as e:
            logger.error(f"  ✗ Error migrating '{tag}': {e}")
            stats["errors"] += 1

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Migration Summary:")
    logger.info(f"  Intents:   {stats['intents']}")
    logger.info(f"  Patterns:  {stats['patterns']}")
    logger.info(f"  Responses: {stats['responses']}")
    logger.info(f"  Errors:    {stats['errors']}")
    logger.info("=" * 60)

    return stats


def main():
    """Main migration function"""
    print("\n" + "=" * 60)
    print(" " * 15 + "JSON to MySQL Migration")
    print("=" * 60 + "\n")

    # Default path
    json_path = AppConfig.DATA_DIR / "intents.json"

    # Check if file exists
    if not json_path.exists():
        print(f"✗ Error: JSON file not found at {json_path}")
        print("Please create intents.json first.")
        return False

    print(f"Source: {json_path}")
    print()

    # Ask for confirmation
    response = input("Clear existing data before migration? (y/N): ").lower()
    clear_existing = response == "y"

    if clear_existing:
        print(
            "\n⚠️  WARNING: This will delete all existing intents, patterns, and responses!"
        )
        confirm = input("Are you sure? Type 'yes' to confirm: ").lower()
        if confirm != "yes":
            print("Migration cancelled.")
            return False

    print()

    # Run migration
    try:
        stats = migrate_intents(str(json_path), clear_existing)

        if stats["errors"] > 0:
            print("\n⚠️  Migration completed with errors")
            return False
        else:
            print("\n✓ Migration completed successfully!")
            return True

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        print(f"\n✗ Migration failed: {e}")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user")
        sys.exit(1)
