# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import asyncio
import os
import json
import logging
import time
from typing import Any, Dict, Optional
import aiosqlite
from motor.motor_asyncio import AsyncIOMotorClient
from config import config

logger = logging.getLogger("Astra.Database")

class Database:
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.sqlite_conn = None
        self.initialized = False

    async def initialize(self):
        if self.initialized:
            return
        
        # Initialize SQLite
        self.sqlite_conn = await aiosqlite.connect(config.SQLITE_PATH)
        await self.sqlite_conn.execute(
            "CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT, updated_at INTEGER)"
        )
        await self.sqlite_conn.commit()

        # Initialize MongoDB
        if config.MONGO_URI:
            try:
                self.mongo_client = AsyncIOMotorClient(config.MONGO_URI)
                # Parse DB name from URI or use default
                db_name = config.MONGO_URI.split('/')[-1].split('?')[0] or "astra_userbot"
                self.mongo_db = self.mongo_client[db_name]
                logger.info("Connected to MongoDB")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                self.mongo_client = None

        await self._sync_on_startup()
        self.initialized = True

    async def _sync_on_startup(self):
        """Syncs data between SQLite and MongoDB."""
        if not self.mongo_db:
            # If no mongo, maybe migrate from JSON to SQLite?
            await self._migrate_from_json()
            return

        logger.info("Starting database synchronization...")
        
        # 1. Get everything from SQLite
        cursor = await self.sqlite_conn.execute("SELECT key, value, updated_at FROM state")
        sqlite_data = {row[0]: {"value": json.loads(row[1]), "updated_at": row[2]} for row in await cursor.fetchall()}
        
        # 2. Get everything from MongoDB
        mongo_data = {}
        async for doc in self.mongo_db.state.find({}):
            mongo_data[doc["_id"]] = {"value": doc["value"], "updated_at": doc.get("updated_at", 0)}

        # 3. Synchronize
        all_keys = set(sqlite_data.keys()) | set(mongo_data.keys())
        
        for key in all_keys:
            s_val = sqlite_data.get(key)
            m_val = mongo_data.get(key)

            if s_val and not m_val:
                # SQLite has it, Mongo doesn't -> Push to Mongo
                await self.mongo_db.state.update_one(
                    {"_id": key}, {"$set": {"value": s_val["value"], "updated_at": s_val["updated_at"]}}, upsert=True
                )
            elif m_val and not s_val:
                # Mongo has it, SQLite doesn't -> Pull to SQLite
                await self.sqlite_conn.execute(
                    "INSERT INTO state (key, value, updated_at) VALUES (?, ?, ?)",
                    (key, json.dumps(m_val["value"]), m_val["updated_at"])
                )
            elif s_val and m_val:
                # Both have it -> Use the latest
                if m_val["updated_at"] > s_val["updated_at"]:
                    await self.sqlite_conn.execute(
                        "UPDATE state SET value = ?, updated_at = ? WHERE key = ?",
                        (json.dumps(m_val["value"]), m_val["updated_at"], key)
                    )
                elif s_val["updated_at"] > m_val["updated_at"]:
                    await self.mongo_db.state.update_one(
                        {"_id": key}, {"$set": {"value": s_val["value"], "updated_at": s_val["updated_at"]}}, upsert=True
                    )

        await self.sqlite_conn.commit()
        logger.info("Database synchronization complete.")

    async def _migrate_from_json(self):
        """Migrates data from bot_state.json if SQLite is empty."""
        json_path = os.path.join(os.path.dirname(config.SQLITE_PATH), "bot_state.json")
        if os.path.exists(json_path):
            cursor = await self.sqlite_conn.execute("SELECT COUNT(*) FROM state")
            count = (await cursor.fetchone())[0]
            if count == 0:
                logger.info("Migrating data from bot_state.json to SQLite...")
                try:
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                        now = int(time.time())
                        for key, val in data.items():
                            await self.sqlite_conn.execute(
                                "INSERT INTO state (key, value, updated_at) VALUES (?, ?, ?)",
                                (key, json.dumps(val), now)
                            )
                        await self.sqlite_conn.commit()
                except Exception as e:
                    logger.error(f"Migration failed: {e}")

    async def get(self, key: str, default: Any = None) -> Any:
        if not self.initialized: await self.initialize()
        cursor = await self.sqlite_conn.execute("SELECT value FROM state WHERE key = ?", (key,))
        row = await cursor.fetchone()
        if row:
            return json.loads(row[0])
        return default

    async def set(self, key: str, value: Any):
        if not self.initialized: await self.initialize()
        now = int(time.time())
        # Update SQLite
        await self.sqlite_conn.execute(
            "INSERT INTO state (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key, json.dumps(value), now)
        )
        await self.sqlite_conn.commit()

        # Update MongoDB (fire and forget or direct?)
        if self.mongo_db:
            asyncio.create_task(
                self.mongo_db.state.update_one(
                    {"_id": key}, {"$set": {"value": value, "updated_at": now}}, upsert=True
                )
            )

    async def delete(self, key: str):
        if not self.initialized: await self.initialize()
        await self.sqlite_conn.execute("DELETE FROM state WHERE key = ?", (key,))
        await self.sqlite_conn.commit()
        if self.mongo_db:
            asyncio.create_task(self.mongo_db.state.delete_one({"_id": key}))

db = Database()
