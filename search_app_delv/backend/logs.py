import logging
import sys

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Ensure logs are sent to stdout
    ]
)

# Get the root logger
logger = logging.getLogger()
logger.info("Logging is configured")
