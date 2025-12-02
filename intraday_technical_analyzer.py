import yfinance as yf
import pandas_ta as ta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
from nsetools import Nse

from logger_config import get_logger
warnings.filterwarnings('ignore')
import pytz

logger = get_logger(__name__)

class IntradayAnalyzer:
    """
    Technical Analysis Class optimized for Intraday Trading with India Timezone
    """
    
    def __init__(self, symbol=None, period="5d", interval="5m", exchange_suffix=".NS"):
        self.symbol = symbol
        self.full_symbol = symbol + exchange_suffix
        self.period = period
        self.interval = interval
        self.data = None
        self.signals = []
        self.indicators_calculated = False
        self.india_tz = pytz.timezone('Asia/Kolkata')
        self.nse = Nse()
    
    def fetch_intraday_data(self):
        """Fetch intraday data with India timezone conversion"""
        try:
            # Use Ticker object to avoid MultiIndex issues
            ticker = yf.Ticker(self.full_symbol)
            self.data = ticker.history(
                period=self.period,
                interval=self.interval,
                prepost=False
            )
            
            if self.data.empty:
                raise ValueError(f"No data found for {self.full_symbol}")
            
            # Convert timezone to India
            self._convert_to_india_timezone()
            
            logger.info(f"Fetched {len(self.data)} intraday bars for {self.full_symbol} (IST Timezone)")
            self.indicators_calculated = False
            return self.data
            
        except Exception as e:
            logger.info(f"Error fetching data for {self.full_symbol}: {e}")
            return None
    
    def _convert_to_india_timezone(self):
        """Convert DataFrame index to India timezone"""
        if self.data is None or self.data.empty:
            return
        
        try:
            # If index is timezone-naive, assume it's UTC and convert to IST
            if self.data.index.tz is None:
                self.data.index = self.data.index.tz_localize('UTC').tz_convert(self.india_tz)
            else:
                self.data.index = self.data.index.tz_convert(self.india_tz)
                
            logger.info(f"✓ Timezone converted to IST: {self.data.index[0]} to {self.data.index[-1]}")
            
        except Exception as e:
            logger.info(f"Timezone conversion failed: {e}")
            try:
                self.data.index = self.data.index.tz_localize(self.india_tz)
                logger.info("✓ Timezone localized to IST")
            except Exception as e2:
                logger.info(f"Timezone localization also failed: {e2}")
    
    def calculate_intraday_indicators(self):
        """
        Calculate indicators with comprehensive error handling and debug info
        """
        if self.data is None:
            self.fetch_intraday_data()
            if self.data is None:
                return None
        
        self.signals = []
        
        try:
            logger.info(f"Calculating indicators for {self.symbol}...")
            
            # 1. BOLLINGER BANDS - with debug info
            try:
                bb_result = self.data.ta.bbands(length=10, std=2.0, append=True)
                if bb_result is not None:
                    # Debug: Check what columns were created
                    bb_columns = [col for col in self.data.columns if 'BB' in col]
                    logger.info(f"    ✓ Bollinger Bands created: {bb_columns}")
                else:
                    logger.info("    ✗ Bollinger Bands returned None")
                    self._add_fallback_bbands()
            except Exception as e:
                logger.info(f"    ✗ Bollinger Bands failed: {e}")
                self._add_fallback_bbands()
            
            # 2. ATR
            try:
                atr_result = self.data.ta.atr(length=6, append=True)
                if atr_result is not None:
                    logger.info("    ✓ ATR calculated")
            except Exception as e:
                logger.info(f"    ✗ ATR failed: {e}")
            
            # 3. RSI
            try:
                rsi_result = self.data.ta.rsi(length=8, append=True)
                if rsi_result is not None:
                    logger.info("    ✓ RSI calculated")
            except Exception as e:
                logger.info(f"    ✗ RSI failed: {e}")
                self._add_fallback_rsi()
            
            # 4. MACD - with detailed debug
            try:
                macd_result = self.data.ta.macd(append=True)
                if macd_result is not None:
                    # Debug MACD values
                    macd_columns = [col for col in self.data.columns if 'MACD' in col]
                    logger.info(f"    ✓ MACD created: {macd_columns}")
                    if len(self.data) > 0:
                        latest = self.data.iloc[-1]
                        macd_line = latest.get('MACD_12_26_9', latest.get('MACD', None))
                        macd_signal = latest.get('MACDs_12_26_9', latest.get('MACD_Signal', None))
                        logger.info(f"    MACD Values - Line: {macd_line}, Signal: {macd_signal}")
                else:
                    logger.info("    ✗ MACD returned None")
                    self._add_fallback_macd()
            except Exception as e:
                logger.info(f"    ✗ MACD failed: {e}")
                self._add_fallback_macd()
            
            # 5. VWAP
            try:
                vwap_result = self.data.ta.vwap(append=True)
                if vwap_result is not None:
                    logger.info("    ✓ VWAP calculated")
            except Exception as e:
                logger.info(f"    ✗ VWAP failed: {e}")
            
            # 6. Williams %R
            try:
                willr_result = self.data.ta.willr(append=True)
                if willr_result is not None:
                    logger.info("    ✓ Williams %R calculated")
            except Exception as e:
                logger.info(f"    ✗ Williams %R failed: {e}")
            
            # 7. Stochastic
            try:
                stoch_result = self.data.ta.stoch(append=True)
                if stoch_result is not None:
                    logger.info("    ✓ Stochastic calculated")
            except Exception as e:
                logger.info(f"    ✗ Stochastic failed: {e}")

            # 8. EMA 9
            try:
                ema_9_result = self.data.ta.ema(length=9, append=True)
                if ema_9_result is not None:
                    logger.info("    ✓ EMA 9 calculated")
            except Exception as e:
                logger.info(f"    ✗ EMA 9 failed: {e}")

            # 9. EMA 21
            try:
                ema_21_result = self.data.ta.ema(length=21, append=True)
                if ema_21_result is not None:
                    logger.info("    ✓ EMA 21 calculated")
            except Exception as e:
                logger.info(f"    ✗ EMA 21 failed: {e}")            
                
            # 10. ADX
            try:
                adx_result = self.data.ta.adx(length=14, append=True)
                if adx_result is not None:
                    logger.info("    ✓ ADX calculated")
            except Exception as e:
                logger.info(f"    ✗ ADX failed: {e}")
            
            self.indicators_calculated = True
            logger.info(f"✓ Indicator calculation completed for {self.symbol}")
            return self.data
            
        except Exception as e:
            logger.info(f"Critical error in indicator calculation: {e}")
            self._calculate_basic_indicators_fallback()
            return self.data
    
    def _add_fallback_bbands(self):
        """Fallback Bollinger Bands calculation"""
        try:
            length = 10
            std = 1.5
            self.data['BB_Middle'] = self.data['Close'].rolling(window=length).mean()
            bb_std = self.data['Close'].rolling(window=length).std()
            self.data['BB_Upper'] = self.data['BB_Middle'] + (bb_std * std)
            self.data['BB_Lower'] = self.data['BB_Middle'] - (bb_std * std)
            logger.info("✓ Fallback Bollinger Bands calculated")
        except Exception as e:
            logger.info(f"✗ Fallback Bollinger Bands failed: {e}")
    
    def _add_fallback_rsi(self):
        """Fallback RSI calculation"""
        try:
            length = 8
            delta = self.data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
            rs = gain / loss
            self.data['RSI_8'] = 100 - (100 / (1 + rs))
            logger.info("✓ Fallback RSI calculated")
        except Exception as e:
            logger.info(f"✗ Fallback RSI failed: {e}")
    
    def _add_fallback_macd(self):
        """Fallback MACD calculation with proper signal determination"""
        try:
            exp1 = self.data['Close'].ewm(span=12).mean()
            exp2 = self.data['Close'].ewm(span=26).mean()
            self.data['MACD_Line'] = exp1 - exp2
            self.data['MACD_Signal'] = self.data['MACD_Line'].ewm(span=9).mean()
            self.data['MACD_Histogram'] = self.data['MACD_Line'] - self.data['MACD_Signal']
            logger.info("✓ Fallback MACD calculated")
        except Exception as e:
            logger.info(f"✗ Fallback MACD failed: {e}")
    
    def _calculate_basic_indicators_fallback(self):
        """Complete fallback when everything else fails"""
        logger.info("Using complete fallback indicator calculation...")
        try:
            self.data['SMA_20'] = self.data['Close'].rolling(window=20).mean()
            self.data['EMA_9'] = self.data['Close'].ewm(span=9).mean()
            self.indicators_calculated = True
            logger.info("✓ Basic fallback indicators calculated")
        except Exception as e:
            logger.info(f"✗ Even basic fallback failed: {e}")
            self.indicators_calculated = False
    
    def _convert_to_native_types(self, value):
        """Convert numpy types to native Python types for JSON serialization"""
        if isinstance(value, (np.float64, np.float32, np.int64, np.int32)):
            return float(value) if 'float' in str(type(value)) else int(value)
        return value
    
    # def generate_intraday_signals(self):
    #     """
    #     Generate trading signals with proper MACD logic
    #     """
    #     if self.data is None or not self.indicators_calculated:
    #         self.calculate_intraday_indicators()
        
    #     if self.data is None:
    #         self.signals = ["ERROR: No data available"]
    #         return self.signals
        
    #     current = self.data.iloc[-1]
    #     signals = []
        
    #     # Get MACD values safely
    #     macd_line = self._get_indicator_safe(current, 'MACD_12_26_9', 'MACD_Line')
    #     macd_signal = self._get_indicator_safe(current, 'MACDs_12_26_9', 'MACD_Signal')
        
    #     # Get other indicators
    #     bb_upper = self._get_indicator_safe(current, 'BBU_10_1.5', 'BB_Upper')
    #     bb_lower = self._get_indicator_safe(current, 'BBL_10_1.5', 'BB_Lower')
    #     rsi_8 = self._get_indicator_safe(current, 'RSI_8')
    #     vwap = self._get_indicator_safe(current, 'VWAP_D')
        
    #     # 1. MACD SIGNALS (FIXED LOGIC)
    #     if macd_line is not None and macd_signal is not None:
    #         if macd_line > macd_signal:
    #             signals.append("MACD_BULLISH: MACD above signal line")
    #         else:
    #             signals.append("MACD_BEARISH: MACD below signal line")
        
    #     # 2. VWAP SIGNALS
    #     if vwap is not None:
    #         if current['Close'] > vwap:
    #             signals.append("ABOVE_VWAP: Bullish intraday trend")
    #         else:
    #             signals.append("BELOW_VWAP: Bearish intraday trend")
        
    #     # 3. RSI SIGNALS
    #     if rsi_8 is not None:
    #         if rsi_8 < 30:
    #             signals.append("RSI_OVERSOLD: Potential buying opportunity")
    #         elif rsi_8 > 70:
    #             signals.append("RSI_OVERBOUGHT: Potential selling opportunity")
    #         elif 30 <= rsi_8 <= 50:
    #             signals.append("RSI_WEAK_BEARISH: Mild bearish momentum")
    #         elif 50 < rsi_8 <= 70:
    #             signals.append("RSI_WEAK_BULLISH: Mild bullish momentum")
        
    #     # 4. BOLLINGER BANDS SIGNALS
    #     if all(x is not None for x in [bb_upper, bb_lower]):
    #         if current['Close'] > bb_upper:
    #             signals.append("BB_BREAKOUT_UP: Above upper band")
    #         elif current['Close'] < bb_lower:
    #             signals.append("BB_BREAKOUT_DOWN: Below lower band")
    #         else:
    #             bb_position = (current['Close'] - bb_lower) / (bb_upper - bb_lower) * 100
    #             if bb_position > 70:
    #                 signals.append("BB_NEAR_UPPER: Close to upper band")
    #             elif bb_position < 30:
    #                 signals.append("BB_NEAR_LOWER: Close to lower band")
        
    #     self.signals = signals
    #     return signals
    

    def generate_intraday_signals(self):
        """
        Generate structured intraday trading signals based on MACD, RSI, VWAP, and Bollinger Bands.
        """
        if self.data is None or not self.indicators_calculated:
            self.calculate_intraday_indicators()

        if self.data is None:
            self.signals = [{"signal": "ERROR", "reason": "No data available"}]
            return self.signals

        current = self.data.iloc[-1]
        signals = []

        # Retrieve indicators safely
        macd_line = self._get_indicator_safe(current, 'MACD_12_26_9', 'MACD_Line')
        macd_signal = self._get_indicator_safe(current, 'MACDs_12_26_9', 'MACD_Signal')
        bb_upper = self._get_indicator_safe(current, 'BBU_10_1.5', 'BB_Upper')
        bb_lower = self._get_indicator_safe(current, 'BBL_10_1.5', 'BB_Lower')
        rsi_8 = self._get_indicator_safe(current, 'RSI_8')
        vwap = self._get_indicator_safe(current, 'VWAP_D')
        adx_14 = self._get_indicator_safe(current, 'ADX_14')

        ts = str(current.name)  # timestamp

        # 1️⃣ MACD SIGNALS
        if macd_line is not None and macd_signal is not None:
            diff = macd_line - macd_signal
            if diff > 0:
                signals.append({"signal": "MACD_TREND_BULLISH", "strength": "STRONG" if diff > 0.05 else "WEAK", "reason": "MACD above signal line", "timestamp": ts})
            else:
                signals.append({"signal": "MACD_TREND_BEARISH", "strength": "STRONG" if abs(diff) > 0.05 else "WEAK", "reason": "MACD below signal line", "timestamp": ts})

        # 2️⃣ VWAP SIGNALS
        if vwap is not None:
            if current["Close"] > vwap:
                signals.append({"signal": "VWAP_POSITION_ABOVE", "reason": "Price above VWAP → bullish bias", "timestamp": ts})
            else:
                signals.append({"signal": "VWAP_POSITION_BELOW", "reason": "Price below VWAP → bearish bias", "timestamp": ts})

        # 3️⃣ ADX TREND STRENGTH
        if adx_14 is not None:
            if adx_14 > 25:
                signals.append({"signal": "TREND_STRENGTH_STRONG", "reason": f"ADX {adx_14:.1f} > 25 → strong trend", "timestamp": ts})
            elif adx_14 < 20:
                signals.append({"signal": "TREND_STRENGTH_WEAK", "reason": f"ADX {adx_14:.1f} < 20 → weak trend", "timestamp": ts})

        # 4️⃣ RSI SIGNALS
        if rsi_8 is not None:
            if rsi_8 < 30:
                signals.append({"signal": "RSI_STATE_OVERSOLD", "reason": "RSI < 30 → potential rebound", "timestamp": ts})
            elif rsi_8 > 70:
                signals.append({"signal": "RSI_STATE_OVERBOUGHT", "reason": "RSI > 70 → potential pullback", "timestamp": ts})
            elif 30 <= rsi_8 < 45:
                signals.append({"signal": "RSI_WEAK_BEARISH", "reason": "RSI mildly bearish", "timestamp": ts})
            elif 55 < rsi_8 <= 70:
                signals.append({"signal": "RSI_WEAK_BULLISH", "reason": "RSI mildly bullish", "timestamp": ts})
            else:
                signals.append({"signal": "RSI_NEUTRAL", "reason": "RSI near midline", "timestamp": ts})

        # 5️⃣ BOLLINGER SIGNALS
        if bb_upper is not None and bb_lower is not None:
            if current["Close"] > bb_upper:
                signals.append({"signal": "BB_BREAKOUT_UPPER", "reason": "Price above upper band", "timestamp": ts})
            elif current["Close"] < bb_lower:
                signals.append({"signal": "BB_BREAKOUT_LOWER", "reason": "Price below lower band", "timestamp": ts})
            else:
                bb_pos = (current["Close"] - bb_lower) / (bb_upper - bb_lower) * 100
                if bb_pos > 70:
                    signals.append({"signal": "BB_NEAR_UPPER", "reason": "Price near upper band", "timestamp": ts})
                elif bb_pos < 30:
                    signals.append({"signal": "BB_NEAR_LOWER", "reason": "Price near lower band", "timestamp": ts})

        self.signals = signals
        return signals

    def _get_indicator_safe(self, current, indicator_name, fallback_name=None):
        """Safely get indicator value with fallback"""
        try:
            if indicator_name in current:
                return current[indicator_name]
            elif fallback_name and fallback_name in current:
                return current[fallback_name]
            else:
                return None
        except:
            return None
    
    def get_intraday_summary(self):
        """
        Get comprehensive intraday analysis summary with proper data types
        """
        if not self.indicators_calculated:
            self.calculate_intraday_indicators()
        
        if self.data is None:
            return {'error': 'No data available'}
        
        current = self.data.iloc[-1]
        logger.info(f"Current row: \n{current}")
        
        # Generate signals if not already done
        if not self.signals:
            self.generate_intraday_signals()
        
        # Safely get all indicator values with native type conversion
        bb_upper = self._get_indicator_safe(current, 'BBU_10_2.0_2.0', 'BB_Upper')
        bb_lower = self._get_indicator_safe(current, 'BBL_10_2.0_2.0', 'BB_Lower')
        bb_middle = self._get_indicator_safe(current, 'BBM_10_2.0_2.0', 'BB_Middle')
        bb_bandwidth = self._get_indicator_safe(current, 'BBB_10_2.0_2.0', 'BB_Bandwidth')
        bb_percentage = self._get_indicator_safe(current, 'BBP_10_2.0_2.0', 'BB_Percentage')
        
        rsi_8 = self._get_indicator_safe(current, 'RSI_8')
        stoch_k = self._get_indicator_safe(current, 'STOCHk_14_3_3')
        williams_r = self._get_indicator_safe(current, 'WILLR_14')
        
        macd_line = self._get_indicator_safe(current, 'MACD_12_26_9', 'MACD_Line')
        macd_signal_line = self._get_indicator_safe(current, 'MACDs_12_26_9', 'MACD_Signal')
        macd_histogram = self._get_indicator_safe(current, 'MACDh_12_26_9', 'MACD_Histogram')
        
        atr = self._get_indicator_safe(current, 'ATRr_6')
        vwap = self._get_indicator_safe(current, 'VWAP_D')
        
        # MACD Analysis with proper logic
        macd_signal_str = "NEUTRAL"
        macd_trend = "NEUTRAL"

        # Trend Indicators
        ema_9 = self._get_indicator_safe(current, 'EMA_9')
        ema_21 = self._get_indicator_safe(current, 'EMA_21')
        adx_14 = self._get_indicator_safe(current, 'ADX_14')
        
        if macd_line is not None and macd_signal_line is not None:
            # FIXED: Proper MACD signal determination
            if macd_line > macd_signal_line:
                macd_signal_str = "BULLISH"
            else:
                macd_signal_str = "BEARISH"
            
            # Trend strength based on histogram
            if macd_histogram is not None:
                hist_abs = abs(macd_histogram)
                if hist_abs > 0.02:  # Adjusted threshold for low-priced stocks
                    macd_trend = "STRONG"
                elif hist_abs > 0.005:
                    macd_trend = "MODERATE"
                else:
                    macd_trend = "WEAK"
        
        # Convert all values to native Python types
        summary = {
            'symbol': self.symbol,
            'full_symbol': self.full_symbol,
            'timestamp': current.name.strftime('%Y-%m-%d %H:%M:%S.%f') if hasattr(current.name, 'strftime') else str(current.name),
            'price_data': {
                'last_price': self._convert_to_native_types(round(current['Close'], 2)),
                'open': self._convert_to_native_types(round(current['Open'], 2)),
                'high': self._convert_to_native_types(round(current['High'], 2)),
                'low': self._convert_to_native_types(round(current['Low'], 2)),
                'VWAP': self._convert_to_native_types(round(vwap, 3)) if vwap is not None else None,
                'ATR_6': self._convert_to_native_types(round(atr, 3)) if atr is not None else None,
            },
            # 'momentum_indicators': {
            #     'RSI_8': self._convert_to_native_types(round(rsi_8, 1)) if rsi_8 is not None else None,
            #     'STOCH_K': self._convert_to_native_types(round(stoch_k, 1)) if stoch_k is not None else None,
            #     'WILLR_14': self._convert_to_native_types(round(williams_r, 1)) if williams_r is not None else None,
            # },
            # 'macd_analysis': {
            #     'macd_line': self._convert_to_native_types(round(macd_line, 4)) if macd_line is not None else None,
            #     'macd_signal_line': self._convert_to_native_types(round(macd_signal_line, 4)) if macd_signal_line is not None else None,
            #     'macd_histogram': self._convert_to_native_types(round(macd_histogram, 4)) if macd_histogram is not None else None,
            #     'MACD_Crossover_Signal': macd_signal_str,
            #     'MACD_Trend_Strength': macd_trend,
            # },
            # 'volatility_indicators': {
            #     'bb_upper': self._convert_to_native_types(round(bb_upper, 2)) if bb_upper is not None else None,
            #     'bb_lower': self._convert_to_native_types(round(bb_lower, 2)) if bb_lower is not None else None,
            #     'bb_middle': self._convert_to_native_types(round(bb_middle, 2)) if bb_middle is not None else None,
            #     'bb_bandwidth': self._convert_to_native_types(round(bb_bandwidth, 2)) if bb_bandwidth is not None else None,
            #     'bb_percentage': self._convert_to_native_types(round(bb_percentage, 2)) if bb_percentage is not None else None,
            # },
            # 'trend_indicators': {
            #     'EMA_9': self._convert_to_native_types(round(ema_9, 2)) if ema_9 is not None else None,
            #     'EMA_21': self._convert_to_native_types(round(ema_21, 2)) if ema_21 is not None else None,
            #     'ADX_14': self._convert_to_native_types(round(adx_14, 2)) if adx_14 is not None else None,
            # },
            # 'trading_signals': self.signals,
            # 'signal_count': len(self.signals),
            'indicators_calculated': self.indicators_calculated,
            'data_points': len(self.data),
            'timezone': 'Asia/Kolkata (IST)'
        }
        # logger.info(f"Generated intraday summary for {self.symbol}: {summary}")
        return summary
    
    def get_stock_news(self):
        ticker = yf.Ticker(self.full_symbol)
        news = ticker.news
        logger.info(f"Generated intraday news for {self.symbol}: {news}")
        return news

    def cleanup(self):
        """Cleanup resources"""
        self.data = None
        self.signals = []
        self.indicators_calculated = False
    
# Test the corrected version
if __name__ == "__main__":
    analyzer = IntradayAnalyzer("AKSHAR", interval="5m")
    summary = analyzer.get_intraday_summary()
    
    logger.info("CORRECTED SUMMARY:")
    import json
    logger.info(json.dumps(summary, indent=2, default=str))