import asyncio
import os
import logging
from dotenv import load_dotenv
from message_bridge.daemon import MessageBridgeDaemon

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

config = {
    'postgres_host': os.getenv('POSTGRES_HOST', 'localhost'),
    'postgres_port': int(os.getenv('POSTGRES_PORT', 5432)),
    'postgres_user': os.getenv('POSTGRES_USER', 'resonant'),
    'postgres_password': os.getenv('POSTGRES_PASSWORD', ''),
    'postgres_db': os.getenv('POSTGRES_DB', 'resonant_dashboard'),
    'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY', ''),
}


async def main():
    daemon = MessageBridgeDaemon(config)
    try:
        await daemon.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await daemon.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await daemon.stop()
        raise


if __name__ == "__main__":
    asyncio.run(main())
