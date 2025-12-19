"""
Logging Configuration for Sniper Trading Bot
Provides colored console output and file logging
"""

import logging
import colorlog
from datetime import datetime
import os
import config

def setup_logger(name="SniperBot"):
    """
    Setup logger with colored console output and file logging
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console Handler with colors
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    console_format = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(asctime)s%(reset)s - %(message)s",
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File Handler for general logs
    file_handler = logging.FileHandler(config.LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter(
        "%(levelname)-8s %(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    # File Handler for errors only
    error_handler = logging.FileHandler(config.ERROR_LOG_FILE, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)
    logger.addHandler(error_handler)
    
    return logger


def log_trade_decision(logger, symbol, stage, result, **kwargs):
    """
    Log trade filtering decision in a structured format
    
    Args:
        logger: Logger instance
        symbol: Trading symbol
        stage: Filter stage (1, 2, or 3)
        result: Pass/Fail result
        **kwargs: Additional information to log
    """
    status = "✅ PASSED" if result.get("pass", False) else "❌ FAILED"
    
    msg = f"[Stage {stage}] {symbol} - {status}"
    
    if "score" in result:
        msg += f" (Score: {result['score']})"
    if "confidence" in result:
        msg += f" (Confidence: {result['confidence']}%)"
    if "reason" in result:
        msg += f" - {result['reason']}"
    
    if result.get("pass", False):
        logger.info(msg)
    else:
        logger.debug(msg)
    
    # Log additional details
    for key, value in kwargs.items():
        logger.debug(f"  {key}: {value}")
    