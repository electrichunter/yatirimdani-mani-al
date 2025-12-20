"""
Sniper Trading Bot için Günlükleme (Logging) Yapılandırması
Renkli konsol çıktısı ve dosya günlüklemesi sağlar
"""

import logging
import colorlog
from datetime import datetime
import os
import config

def setup_logger(name="SniperBot"):
    """
    Renkli konsol çıktısı ve dosya günlüklemesi ile logger'ı kurar
    
    Argümanlar:
        name: Logger adı
        
    Döner:
        Yapılandırılmış logger nesnesi
    """
    # Mevcut değilse logs dizinini oluştur
    os.makedirs("logs", exist_ok=True)
    
    # Logger oluştur
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Mükerrer işleyicileri önle
    if logger.handlers:
        return logger
    
    # Renkli Konsol İşleyicisi
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
    
    # Genel günlükler için Dosya İşleyicisi
    file_handler = logging.FileHandler(config.LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter(
        "%(levelname)-8s %(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    # Sadece hatalar için Dosya İşleyicisi
    error_handler = logging.FileHandler(config.ERROR_LOG_FILE, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)
    logger.addHandler(error_handler)
    
    return logger


def log_trade_decision(logger, symbol, stage, result, **kwargs):
    """
    Ticaret filtreleme kararını yapılandırılmış bir formatta günlükler
    
    Argümanlar:
        logger: Logger nesnesi
        symbol: Ticari varlık
        stage: Filtre aşaması (1, 2 veya 3)
        result: Geçti/Kaldı sonucu
        **kwargs: Günlüklenmek istenen ek bilgiler
    """
    status = "✅ GEÇTİ" if result.get("pass", False) or result.get("decision") != "PASS" else "❌ KALDI"
    
    msg = f"[{stage}. Aşama] {symbol} - {status}"
    
    if "score" in result:
        msg += f" (Skor: {result['score']})"
    if "confidence" in result:
        msg += f" (Güven: %{result['confidence']})"
    if "reason" in result:
        msg += f" - {result['reason']}"
    
    if result.get("pass", False) or result.get("decision") != "PASS":
        logger.info(msg)
    else:
        logger.debug(msg)
    
    # Ek detayları günlükle
    for key, value in kwargs.items():
        logger.debug(f"  {key}: {value}")