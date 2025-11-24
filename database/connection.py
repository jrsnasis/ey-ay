# ey-ay/database/connection.py

from mysql.connector import pooling, Error
from contextlib import contextmanager
import sys
from pathlib import Path
from config.settings import DatabaseConfig
from config.logging_config import get_logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = get_logger(__name__)


class DatabaseConnection:
    _pool = None

    def __init__(self):
        """Initialize database connection pool"""
        if DatabaseConnection._pool is None:
            self._create_pool()
        logger.info("Database connection manager initialized")

    def _create_pool(self):
        """Create connection pool"""
        try:
            logger.info("Creating MySQL connection pool...")
            logger.debug(
                f"Connecting to {DatabaseConfig.HOST}:{DatabaseConfig.PORT}/{DatabaseConfig.NAME}"
            )

            pool_config = {
                "pool_name": "chatbot_pool",
                "pool_size": DatabaseConfig.POOL_SIZE,
                "pool_reset_session": True,
                "host": DatabaseConfig.HOST,
                "port": DatabaseConfig.PORT,
                "database": DatabaseConfig.NAME,
                "user": DatabaseConfig.USER,
                "password": DatabaseConfig.PASSWORD,
                "charset": "utf8mb4",
                "use_unicode": True,
                "autocommit": False,
                "raise_on_warnings": True,
            }

            DatabaseConnection._pool = pooling.MySQLConnectionPool(**pool_config)
            logger.info(
                f"Connection pool created successfully (size: {DatabaseConfig.POOL_SIZE})"
            )

        except Error as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = DatabaseConnection._pool.get_connection()
            logger.debug("Connection acquired from pool")

            yield conn

            # Commit if no errors
            conn.commit()
            logger.debug("Transaction committed")

        except Error as e:
            if conn:
                conn.rollback()
                logger.warning("Transaction rolled back due to error")
            logger.error(f"Database error: {e}")
            raise

        except Exception as e:
            if conn:
                conn.rollback()
                logger.warning("Transaction rolled back due to error")
            logger.error(f"Unexpected error: {e}")
            raise

        finally:
            if conn:
                conn.close()
                logger.debug("Connection returned to pool")

    def test_connection(self) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                cursor.close()

                if result and result[0] == 1:
                    logger.info("✓ Database connection test: SUCCESS")
                    return True
                else:
                    logger.error(
                        "✗ Database connection test: FAILED (unexpected result)"
                    )
                    return False

        except Exception as e:
            logger.error(f"✗ Database connection test: FAILED - {e}")
            return False


# Singleton instance
_db_instance = None


def get_db() -> DatabaseConnection:
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseConnection()
    return _db_instance


if __name__ == "__main__":
    print("=" * 60)
    print("Testing MySQL Database Connection")
    print("=" * 60)

    try:
        db = DatabaseConnection()

        # Test connection
        print("\n1. Testing connection...")
        if db.test_connection():
            print("   ✓ Connection successful!")
        else:
            print("   ✗ Connection failed!")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
