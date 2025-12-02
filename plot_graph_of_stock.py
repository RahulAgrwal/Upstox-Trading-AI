import matplotlib
matplotlib.use('Agg')  # <-- ADD THIS LINE FIRST

import yfinance as yf
import mplfinance as mpf
from datetime import datetime, timedelta
import pandas as pd
import pytz 
import pandas_ta as ta
import os
class StockChartAnalyzer:
    """A class to fetch, analyze, and plot stock data with technical indicators."""
    
    def __init__(self, ticker="IEX",  days=1,interval="5m",exchange_suffix=".NS"):
        """
        Initialize the StockChartAnalyzer.
        
        Args:
            ticker (str): Stock ticker symbol
            interval (str): Data interval (1m, 5m, 15m, 1h, 1d, etc.)
            days (int): Number of days of historical data to fetch
        """
        self.ticker = ticker + exchange_suffix
        self.interval = interval
        self.days = days
        self.ohlcv_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        self.data = None
        self.data_clean = None
        self.file_name = f'charts/{self.ticker}_{self.interval}_{self.days}D_chart.png'
        self.chart_title = None
        
    
    def fetch_data(self):
        """
        Fetch stock data from Yahoo Finance.
        
        Returns:
            bool: True if successful, False otherwise
        """

        try:
            self.data = yf.download(
                self.ticker,
                period=self.days,
                interval=self.interval,
                prepost=False,
            )
            
            if self.data.empty:
                print("🛑 ERROR: The fetched DataFrame is empty.")
                return False
                
            return True
            
        except Exception as e:
            print(f"🛑 ERROR: Failed to fetch data: {e}")
            return False
    
    def normalize_columns(self):
        """Normalize column names from MultiIndex to simple strings."""
        if self.data is None:
            print("🛑 ERROR: No data available for column normalization.")
            return False
            
        new_columns = []
        for col in self.data.columns:
            if isinstance(col, tuple):
                new_col_name = str(col[0]).capitalize()
            else:
                new_col_name = str(col).capitalize()
            new_columns.append(new_col_name)
        
        self.data.columns = new_columns
        
        # Check for required columns
        missing_cols = [col for col in self.ohlcv_cols if col not in self.data.columns]
        if missing_cols:
            print(f"🛑 ERROR: Data is missing required columns: {missing_cols}")
            print(f"Final available columns are: {list(self.data.columns)}")
            return False
            
        return True
    
    def clean_data(self):
        """
        Clean and preprocess the data.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.data is None:
            print("🛑 ERROR: No data available for cleaning.")
            return False
            
        self.data_clean = self.data.copy()
        
        # Timezone conversion
        try:
            ist_tz = pytz.timezone('Asia/Kolkata')
            if self.data_clean.index.tz is None:
                self.data_clean.index = self.data_clean.index.tz_localize(ist_tz, ambiguous='infer')
            else:
                self.data_clean.index = self.data_clean.index.tz_convert(ist_tz)
        except Exception as tz_error:
            print(f"⚠️ Warning: Timezone conversion failed. Error: {tz_error}")
        
        # Ensure correct data types and drop NaNs
        self.data_clean.loc[:, self.ohlcv_cols] = self.data_clean[self.ohlcv_cols].astype('float64')
        self.data_clean.dropna(subset=self.ohlcv_cols, inplace=True)
        start_date_str = self.data_clean.index[0]
        end_date_str = self.data_clean.index[-1]
        self.chart_title = f"{self.ticker} | {self.interval} | From {start_date_str} to {end_date_str}.." 
        print(f"✅ Data cleaned. Date range: {start_date_str} to {end_date_str}")
 
        if self.data_clean.empty:
            print("⚠️ Data became empty after cleaning. Cannot plot.")
            return False
            
        return True
    
    def calculate_indicators(self):
        """
        Calculate technical indicators.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.data_clean is None:
            print("🛑 ERROR: No cleaned data available for indicator calculation.")
            return False
            
        try:
            # SuperTrend
            st = self.data_clean.ta.supertrend(length=10, multiplier=3, append=True)
            st_main_col = [col for col in st.columns if col.startswith('SUPERT_')][0]
            self.data_clean[st_main_col] = st[st_main_col]
            
            # RSI
            self.data_clean['RSI'] = ta.rsi(self.data_clean['Close'], length=14)
            
            # Moving Averages
            self.data_clean['SMA_20'] = self.data_clean.ta.sma(20)
            self.data_clean['SMA_50'] = self.data_clean.ta.sma(50)
            
            # --- NEW: VWAP ---
            # VWAP calculation needs 'High', 'Low', 'Close', 'Volume'
            # Note: VWAP for yfinance intraday data can be cumulative from start of history, 
            # for true daily VWAP, the function ta.vwap() resets daily (which is preferred for intraday)
            self.data_clean['VWAP'] = ta.vwap(
                high=self.data_clean['High'], 
                low=self.data_clean['Low'], 
                close=self.data_clean['Close'], 
                volume=self.data_clean['Volume']
            )
            
            # --- NEW: EMAs (9 and 21) ---
            self.data_clean['EMA_9'] = self.data_clean.ta.ema(9)
            self.data_clean['EMA_21'] = self.data_clean.ta.ema(21)
            
            # --- NEW: MACD ---
            # Default settings are: fast=12, slow=26, signal=9
            macd_df = self.data_clean.ta.macd(fast=12, slow=26, signal=9, append=True)
            
            # The columns created are typically MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
            # We'll rename them for easier use:
            self.data_clean['MACD_Line'] = macd_df.iloc[:, 0]
            self.data_clean['MACD_Hist'] = macd_df.iloc[:, 1]
            self.data_clean['MACD_Signal'] = macd_df.iloc[:, 2]

            print(f"✅ Indicators calculated. Final columns: {list(self.data_clean.columns)}")
            return True
            
        except Exception as e:
            print(f"🛑 ERROR: Failed to calculate indicators: {e}")
            return False
    
    def create_addplots(self):
        """
        Create additional plots for technical indicators.
        
        Returns:
            list: List of addplot objects
        """
        if self.data_clean is None or self.data_clean.empty:
            print("⚠️ No data to create addplots.")
            return []
            
        try:
            # Find SuperTrend column
            st_main_col = [col for col in self.data_clean.columns if col.startswith('SUPERT_')][0]
            
            # --- Get last values for labels ---
            # (We use .iloc[-1] to get the last row's value)
            last_st = self.data_clean[st_main_col].iloc[-1]
            last_sma_20 = self.data_clean['SMA_20'].iloc[-1]
            last_sma_50 = self.data_clean['SMA_50'].iloc[-1]
            last_vwap = self.data_clean['VWAP'].iloc[-1]
            last_ema_9 = self.data_clean['EMA_9'].iloc[-1]
            last_ema_21 = self.data_clean['EMA_21'].iloc[-1]
            last_rsi = self.data_clean['RSI'].iloc[-1]
            last_macd_line = self.data_clean['MACD_Line'].iloc[-1]
            last_macd_signal = self.data_clean['MACD_Signal'].iloc[-1]
            last_macd_hist = self.data_clean['MACD_Hist'].iloc[-1]

            # 1. Calculate the difference (change) between the current and previous bar
            hist_diff = self.data_clean['MACD_Hist'].diff()
            
            # 2. Define colors
            macd_colors = [
                'green' if bar >= 0 and diff > 0 else 
                'lightcoral' if bar < 0 and diff > 0 else 
                'red' if bar <= 0 and diff < 0 else 
                'lightgreen' # For bars above zero that are decreasing
                for bar, diff in zip(self.data_clean['MACD_Hist'], hist_diff)
            ]
            
            add_plots = [
                # SuperTrend
                mpf.make_addplot(
                    self.data_clean[st_main_col], 
                    color='navy', 
                    linestyle='-', 
                    width=2,
                    label=f'SuperTrend(10,3): {last_st:.2f}'
                ),
                # Moving Averages
                mpf.make_addplot(
                    self.data_clean['SMA_20'], 
                    color='orange', 
                    label=f'SMA 20: {last_sma_20:.2f}'
                ),
                mpf.make_addplot(
                    self.data_clean['SMA_50'], 
                    color='red', 
                    label=f'SMA 50: {last_sma_50:.2f}'
                ),
                
                # --- NEW: VWAP ---
                mpf.make_addplot(
                    self.data_clean['VWAP'], 
                    color='purple', 
                    linestyle='--', 
                    width=1,
                    label=f'VWAP: {last_vwap:.2f}'
                ),
                
                # --- NEW: EMAs ---
                mpf.make_addplot(
                    self.data_clean['EMA_9'], 
                    color='blue', 
                    width=1,
                    label=f'EMA 9: {last_ema_9:.2f}'
                ),
                mpf.make_addplot(
                    self.data_clean['EMA_21'], 
                    color='magenta', 
                    width=1,
                    label=f'EMA 21: {last_ema_21:.2f}'
                ),
                
                # RSI in separate panel
                mpf.make_addplot(
                    self.data_clean['RSI'], 
                    panel=1, 
                    color='brown', 
                    ylabel='RSI', 
                    label=f'RSI 14: {last_rsi:.2f}'
                ),
                # --- NEW: MACD Line in panel 2 ---
                mpf.make_addplot(
                    self.data_clean['MACD_Line'], 
                    panel=2, 
                    color='blue', 
                    width=1.0,
                    ylabel='MACD', 
                    label=f'MACD: {last_macd_line:.2f}'
                ),
                
                # --- NEW: MACD Signal Line in panel 2 ---
                mpf.make_addplot(
                    self.data_clean['MACD_Signal'], 
                    panel=2, 
                    color='red', 
                    width=1.0,
                    label=f'Signal: {last_macd_signal:.2f}'
                ),

                # --- NEW: MACD Histogram in panel 2 (as a bar plot) ---
                mpf.make_addplot(
                    self.data_clean['MACD_Hist'], 
                    type='bar', 
                    panel=2,
                    color=macd_colors,
                    width=0.7,
                    alpha=0.8,
                    secondary_y=False,
                    label=f'Hist: {last_macd_hist:.2f}'
                )
            ]
            
            return add_plots
            
        except Exception as e:
            print(f"🛑 ERROR: Failed to create addplots: {e}")
            # This can happen if iloc[-1] fails on a short/empty dataframe
            return []
    
    def plot_chart(self, save_file=True):
        """
        Generate and save the candlestick chart with indicators.
        
        Args:
            save_file (bool): Whether to save the chart to file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.data_clean is None:
            print("🛑 ERROR: No cleaned data available for plotting.")
            return False
            
        try:
            # Create market colors and style
            mc = mpf.make_marketcolors(up='g', down='r', inherit=True)
            s = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc)
            
            # Get additional plots
            add_plots = self.create_addplots()
            
            # Plot configuration
            plot_kwargs = {
                'type': 'candle',
                'style': s,
                'title': self.chart_title,
                'ylabel': 'Price (₹)',
                'volume': True,
                'volume_panel': 3,
                'show_nontrading': False,
                'addplot': add_plots,
                'xrotation': 10,
                'tight_layout': True,
                'figsize': (30, 20),
                'panel_ratios': (4, 1, 2, 1),  # Price chart taller than volume
            }
            
            if save_file:
                directory = os.path.dirname(self.file_name)
                if directory and not os.path.exists(directory):
                    print(f"📁 Creating directory: {directory}")
                    os.makedirs(directory, exist_ok=True)
                plot_kwargs['savefig'] = self.file_name
            
            # Generate plot
            mpf.plot(self.data_clean, **plot_kwargs)
            
            if save_file:
                print(f"✅ Chart with labeled indicators saved as {self.file_name}")
            else:
                print("✅ Chart generated successfully.")
                
            return True
            
        except Exception as e:
            print(f"🛑 ERROR: Failed to plot chart: {e}")
            return False
    
    def generate_chart(self):
        """
        Execute the complete analysis pipeline.
        
        Returns:
            bool: True if successful, False otherwise
        """
        steps = [
            ("Fetching data", self.fetch_data),
            ("Normalizing columns", self.normalize_columns),
            ("Cleaning data", self.clean_data),
            ("Calculating indicators", self.calculate_indicators),
            ("Plotting chart", self.plot_chart)
        ]
        
        for step_name, step_func in steps:
            print(f"\n--- {step_name} ---")
            if not step_func():
                print(f"❌ Analysis failed at: {step_name}")
                return False
        
        return True
    def get_chart_file_name(self):
        """Get the file name of the saved chart."""
        return self.file_name

    def destroy(self):
        """Clean up large dataframes and close matplotlib figures."""
        try:
            # Delete dataframes
            del self.data
            del self.data_clean

            # Close all open matplotlib figures
            import matplotlib.pyplot as plt
            plt.close('all')

            # Delete other attributes (optional)
            del self.ticker
            del self.file_name
            del self.chart_title

            print("🧹 Resources cleaned up successfully.")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

if __name__ == "__main__":
    # Basic usage
    analyzer = StockChartAnalyzer(ticker="IEX", days="3d", interval="5m")
    analyzer.generate_chart()
    print("File Name: ", analyzer.file_name)
    
    # Custom usage
    analyzer = StockChartAnalyzer(ticker="RELIANCE", days="3d", interval="15m")
    success = analyzer.generate_chart()
    # Access the data if needed
    # if analyzer.data_clean is not None:
    #     print(analyzer.data_clean.head())