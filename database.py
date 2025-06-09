import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
from config import Config


class DatabaseManager:
    """Manages all database operations for Labubu Monitor"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DB_PATH
        self.init_database()

    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Stock events table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS stock_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    product_name TEXT,
                    has_stock INTEGER NOT NULL,
                    price TEXT,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Notifications table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Monitor settings table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS monitor_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    product_name TEXT,
                    target_price REAL,
                    last_checked DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.commit()
            logging.info("Database initialized successfully")

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()

    def log_stock_event(
        self, url: str, has_stock: bool, product_name: str = None, price: str = None
    ) -> int:
        """Log a stock checking event"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO stock_events 
                (url, product_name, has_stock, price, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """,
                (url, product_name, has_stock, price, datetime.utcnow()),
            )
            conn.commit()
            event_id = cursor.lastrowid

            logging.info(
                f"Stock event logged: {url} stock={has_stock} "
                f"product={product_name} price={price}"
            )
            return event_id

    def log_notification(
        self, url: str, notification_type: str, status: str, message: str = None
    ) -> int:
        """Log a notification attempt"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO notifications 
                (url, notification_type, status, message, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """,
                (url, notification_type, status, message, datetime.utcnow()),
            )
            conn.commit()
            return cursor.lastrowid

    def get_recent_events(self, limit: int = 100) -> List[Dict]:
        """Get recent stock events"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM stock_events 
                ORDER BY timestamp DESC 
                LIMIT ?
            """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_stock_history(self, url: str, hours: int = 24) -> List[Dict]:
        """Get stock history for a specific URL"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM stock_events 
                WHERE url = ? AND timestamp > datetime('now', '-{} hours')
                ORDER BY timestamp DESC
            """.format(
                    hours
                ),
                (url,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_notification_stats(self, hours: int = 24) -> Dict:
        """Get notification statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    notification_type,
                    status,
                    COUNT(*) as count
                FROM notifications 
                WHERE timestamp > datetime('now', '-{} hours')
                GROUP BY notification_type, status
            """.format(
                    hours
                )
            )

            stats = {}
            for row in cursor.fetchall():
                ntype = row["notification_type"]
                if ntype not in stats:
                    stats[ntype] = {}
                stats[ntype][row["status"]] = row["count"]

            return stats

    def add_monitor_url(self, url: str, product_name: str = None) -> bool:
        """Add or update a URL to monitor"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO monitor_settings 
                (url, product_name, updated_at)
                VALUES (?, ?, ?)
            """,
                (url, product_name, datetime.utcnow()),
            )
            conn.commit()
            return True

    def get_monitor_urls(self) -> List[Dict]:
        """Get all active monitor URLs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM monitor_settings 
                WHERE is_active = 1
                ORDER BY created_at
            """
            )
            return [dict(row) for row in cursor.fetchall()]

    def update_last_checked(self, url: str):
        """Update last checked timestamp for a URL"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE monitor_settings 
                SET last_checked = ?, updated_at = ?
                WHERE url = ?
            """,
                (datetime.utcnow(), datetime.utcnow(), url),
            )
            conn.commit()
