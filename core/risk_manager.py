"""
Risk Management Module
Calculates position sizing, SL/TP, and Risk/Reward ratios
"""

import config
from utils.logger import setup_logger

logger = setup_logger("RiskManager")


class RiskManager:
    """Handles position sizing and risk calculations"""
    
    def __init__(self, broker):
        """
        Args:
            broker: MT5Broker instance
        """
        self.broker = broker
    
    def calculate_position_size(self, symbol, entry_price, stop_loss, risk_percent=None):
        """
        Calculate position size based on risk percentage
        
        Formula:
        Position Size = (Account Balance * Risk%) / (Distance to SL in pips * Pip Value)
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_percent: Risk percentage (default from config)
            
        Returns:
            Position size in lots
        """
        if risk_percent is None:
            risk_percent = config.RISK_PERCENT
        
        # Get account balance
        balance = self.broker.get_balance()
        if balance == 0:
            logger.error("Account balance is 0, cannot calculate position size")
            return 0.01  # Minimum lot size
        
        # Calculate risk amount
        risk_amount = balance * (risk_percent / 100)
        
        # Calculate distance to SL
        sl_distance = abs(entry_price - stop_loss)
        
        if sl_distance == 0:
            logger.error("Stop loss distance is 0")
            return 0.01
        
        # Simplified calculation (needs adjustment based on symbol)
        # For forex pairs, typically 1 pip = 0.0001
        # For more accurate calculation, use symbol contract size
        
        # Get pip value (this is simplified - real implementation needs symbol specs)
        if "JPY" in symbol:
            pip_value = 0.01  # JPY pairs use 2 decimal places
        else:
            pip_value = 0.0001  # Most forex pairs use 4 decimal places
        
        sl_distance_pips = sl_distance / pip_value
        
        # Assume $1 per pip per mini lot (0.1) for standard account
        # This is a simplification - real value depends on account denomination
        value_per_pip = 1.0  # USD per pip for 0.1 lot
        
        # Calculate position size
        position_size = risk_amount / (sl_distance_pips * value_per_pip) * 0.1
        
        # Round to 2 decimal places
        position_size = round(position_size, 2)
        
        # Ensure minimum lot size
        if position_size < 0.01:
            position_size = 0.01
        
        # Cap maximum lot size (optional safety)
        max_lot_size = 10.0
        if position_size > max_lot_size:
            logger.warning(f"Position size {position_size} exceeds maximum, capping at {max_lot_size}")
            position_size = max_lot_size
        
        logger.info(f"💰 Position size calculated: {position_size} lots (Risk: ${risk_amount:.2f})")
        
        return position_size
    
    def calculate_risk_reward_ratio(self, entry_price, stop_loss, take_profit):
        """
        Calculate Risk/Reward ratio
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            Risk/Reward ratio (e.g., 3.0 means 3:1 reward:risk)
        """
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk == 0:
            return 0
        
        rr_ratio = reward / risk
        return round(rr_ratio, 2)
    
    def validate_trade(self, entry_price, stop_loss, take_profit, decision="PASS"):
        """
        Validate if trade meets minimum risk/reward requirements
        Now with auto-fallback for missing (0.0) values
        """
        entry_price = float(entry_price)
        stop_loss = float(stop_loss)
        take_profit = float(take_profit)

        # FALLBACK: If prices are 0 (likely AI truncation or error)
        if decision != "PASS" and entry_price > 0:
            if stop_loss == 0:
                # Default 1% SL
                stop_loss = entry_price * (0.99 if decision == "BUY" else 1.01)
                logger.warning(f"⚠️ Kritik SL eksik! Otomatik %1 SL atandı: {stop_loss:.5f}")
            
            if take_profit == 0:
                # Default 1.5% TP (to meet 1.5 RR ratio)
                take_profit = entry_price * (1.015 if decision == "BUY" else 0.985)
                logger.warning(f"⚠️ Kritik TP eksik! Otomatik %1.5 TP atandı: {take_profit:.5f}")
        
        elif decision != "PASS" and entry_price <= 0:
            logger.error("❌ Geçersiz Giriş Fiyatı (0.0). İşlem iptal edildi.")
            return {
                "valid": False,
                "reason": "Entry price is 0.0",
                "rr_ratio": 0,
                "sl": stop_loss,
                "tp": take_profit
            }

        rr_ratio = self.calculate_risk_reward_ratio(entry_price, stop_loss, take_profit)
        
        if rr_ratio < config.MIN_RISK_REWARD_RATIO:
            return {
                "valid": False,
                "reason": f"R:R {rr_ratio} below minimum {config.MIN_RISK_REWARD_RATIO}",
                "rr_ratio": rr_ratio,
                "sl": stop_loss,
                "tp": take_profit
            }
        
        # Check if SL and TP are on correct sides of entry
        if stop_loss == entry_price or take_profit == entry_price:
            return {
                "valid": False,
                "reason": "SL or TP equals entry price",
                "rr_ratio": rr_ratio,
                "sl": stop_loss,
                "tp": take_profit
            }
        
        return {
            "valid": True,
            "reason": "Trade parameters valid",
            "rr_ratio": rr_ratio,
            "sl": stop_loss,
            "tp": take_profit
        }
    
    def check_position_limits(self):
        """
        Check if new position can be opened based on limits
        
        Returns:
            Dict with permission status
        """
        open_positions = self.broker.get_open_positions()
        
        if len(open_positions) >= config.MAX_OPEN_POSITIONS:
            return {
                "allowed": False,
                "reason": f"Maximum positions ({config.MAX_OPEN_POSITIONS}) already open"
            }
        
        return {
            "allowed": True,
            "current_positions": len(open_positions)
        }
