"""
MT5 Broker Connection and Order Execution
Handles all MetaTrader 5 interactions
"""

import MetaTrader5 as mt5
from datetime import datetime
import config
from utils.logger import setup_logger

logger = setup_logger("MT5Broker")


class MT5Broker:
    """MetaTrader 5 broker connection manager"""
    
    def __init__(self):
        self.initialized = False
        self.account_info = None
        self.connect()
    
    def connect(self):
        """Initialize MT5 connection"""
        try:
            # Initialize MT5
            if config.MT5_PATH:
                if not mt5.initialize(path=config.MT5_PATH):
                    raise Exception(f"MT5 initialization failed: {mt5.last_error()}")
            else:
                if not mt5.initialize():
                    raise Exception(f"MT5 initialization failed: {mt5.last_error()}")
            
            # Login
            if config.MT5_LOGIN and config.MT5_PASSWORD and config.MT5_SERVER:
                authorized = mt5.login(
                    login=config.MT5_LOGIN,
                    password=config.MT5_PASSWORD,
                    server=config.MT5_SERVER
                )
                if not authorized:
                    raise Exception(f"MT5 login failed: {mt5.last_error()}")
                
                logger.info(f"✅ Connected to MT5: {config.MT5_SERVER}")
            else:
                logger.warning("⚠️ MT5 credentials not configured, using default account")
            
            self.initialized = True
            self.update_account_info()
            
        except Exception as e:
            logger.error(f"❌ MT5 connection failed: {str(e)}")
            self.initialized = False
    
    def update_account_info(self):
        """Fetch current account information"""
        if not self.initialized:
            return None
        
        account = mt5.account_info()
        if account is None:
            logger.error(f"Failed to get account info: {mt5.last_error()}")
            return None
        
        self.account_info = {
            "balance": account.balance,
            "equity": account.equity,
            "margin": account.margin,
            "free_margin": account.margin_free,
            "profit": account.profit
        }
        
        return self.account_info
    
    def get_balance(self):
        """Get current account balance"""
        self.update_account_info()
        return self.account_info["balance"] if self.account_info else 0
    
    def get_open_positions(self):
        """Get list of currently open positions"""
        if not self.initialized:
            return []
        
        positions = mt5.positions_get()
        if positions is None:
            return []
        
        return [
            {
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "type": "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                "volume": pos.volume,
                "price_open": pos.price_open,
                "sl": pos.sl,
                "tp": pos.tp,
                "profit": pos.profit
            }
            for pos in positions
        ]
    
    def place_order(self, symbol, action, volume, entry=None, sl=None, tp=None, comment=""):
        """
        Place a market order
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            action: "BUY" or "SELL"
            volume: Lot size (e.g., 0.01)
            entry: Entry price (None for market order)
            sl: Stop Loss price
            tp: Take Profit price
            comment: Order comment
            
        Returns:
            Dict with success status and order details
        """
        if not self.initialized:
            return {"success": False, "error": "MT5 not initialized"}
        
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return {"success": False, "error": f"Symbol {symbol} not found"}
        
        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                return {"success": False, "error": f"Failed to select {symbol}"}
        
        # Prepare request
        order_type = mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL
        price = entry if entry else (symbol_info.ask if action == "BUY" else symbol_info.bid)
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl if sl else 0,
            "tp": tp if tp else 0,
            "deviation": 20,
            "magic": 234000,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send order
        result = mt5.order_send(request)
        
        if result is None:
            return {"success": False, "error": f"Order send failed: {mt5.last_error()}"}
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {
                "success": False,
                "error": f"Order failed with retcode {result.retcode}: {result.comment}"
            }
        
        return {
            "success": True,
            "ticket": result.order,
            "volume": result.volume,
            "price": result.price,
            "comment": result.comment
        }
    
    def close(self):
        """Shutdown MT5 connection"""
        if self.initialized:
            mt5.shutdown()
            logger.info("MT5 connection closed")
            self.initialized = False
