import logging
import watchtower

logger = logging.getLogger("quicktrack")
logger.setLevel(logging.INFO)
logger.addHandler(watchtower.CloudWatchLogHandler(log_group="QuickTrackLogs"))

def log_event(message):
    logger.info(message)