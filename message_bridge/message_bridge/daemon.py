import asyncio
import asyncpg
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageBridgeDaemon:
    def __init__(self, config):
        self.config = config
        self.pool = None
        self.running = False

    async def start(self):
        logger.info("🚀 Starting Message Bridge Daemon...")
        self.pool = await asyncpg.create_pool(
            host=self.config['postgres_host'],
            port=self.config['postgres_port'],
            user=self.config['postgres_user'],
            password=self.config['postgres_password'],
            database=self.config['postgres_db'],
            min_size=2,
            max_size=10
        )
        logger.info("✅ Database connection pool established")

        self.running = True
        await self.listen_loop()

    async def listen_loop(self):
        async with self.pool.acquire() as conn:
            def callback(conn, pid, channel, payload):
                asyncio.create_task(self.handle_notification(payload))

            await conn.add_listener('message_created', callback)
            logger.info("🎧 Listening for message_created notifications...")

            while self.running:
                await asyncio.sleep(1)

    async def handle_notification(self, payload):
        try:
            data = json.loads(payload)
            message_id = data['id']
            logger.info(f"📨 Received message: {message_id}")

            from .processor import MessageProcessor
            processor = MessageProcessor(self.pool, self.config)
            await processor.process(message_id)

        except Exception as e:
            logger.error(f"❌ Error handling notification: {e}")

    async def stop(self):
        self.running = False
        if self.pool:
            await self.pool.close()
        logger.info("Message Bridge stopped")
