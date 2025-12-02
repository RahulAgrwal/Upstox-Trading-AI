import yfinance as yf
import pandas as pd
import time
from datetime import datetime

class NSETickersData:
    def __init__(self):
        self.results = []
    
    def get_symbols(self):
        """Get your NSE 500 symbols here"""
        # Replace this with your actual 500 NSE stocks
        return [
            'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS',
            'ICICIBANK.NS', 'KOTAKBANK.NS', 'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS',
            # Add all 500 stocks...
        ]
    
    def fetch_stock_data(self, symbols, batch_size=50):
        """Fetch comprehensive data using Tickers in batches"""
        all_results = []
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            batch_number = i//batch_size + 1
            total_batches = (len(symbols)-1)//batch_size + 1
            
            print(f"Batch {batch_number}/{total_batches}: Processing {len(batch)} stocks...")
            
            batch_results = self._process_batch(batch)
            all_results.extend(batch_results)
            
            # Progress update
            success_count = len([r for r in batch_results if r['LTP'] != 'N/A'])
            print(f"  ✓ Success: {success_count}/{len(batch)}")
            
            # Delay between batches
            if i + batch_size < len(symbols):
                time.sleep(1)
        
        return all_results
    
    def _process_batch(self, batch_symbols):
        """Process a single batch of symbols"""
        try:
            # Create Tickers object
            tickers = yf.Tickers(" ".join(batch_symbols))
            
            batch_results = []
            for symbol in batch_symbols:
                result = self._get_single_stock_data(tickers, symbol)
                batch_results.append(result)
            
            return batch_results
            
        except Exception as e:
            print(f"  ✗ Batch error: {e}")
            # Fallback to individual processing
            return [self._get_individual_fallback(symbol) for symbol in batch_symbols]
    
    def _get_single_stock_data(self, tickers, symbol):
        """Get data for single stock from Tickers object"""
        try:
            base_symbol = symbol.replace('.NS', '')
            ticker = tickers.tickers[symbol]
            info = ticker.info
            print(info)
            
            # Get price data
            ltp = (info.get('currentPrice') or 
                  info.get('regularMarketPrice') or 
                  info.get('previousClose'))
            
            # Calculate change
            prev_close = info.get('previousClose', 0)
            if ltp and prev_close and ltp != 'N/A' and prev_close != 'N/A':
                change = ltp - prev_close
                change_pct = (change / prev_close) * 100
            else:
                change = 'N/A'
                change_pct = 'N/A'
            
            # Get additional data
            volume = info.get('volume', 'N/A')
            market_cap = info.get('marketCap', 'N/A')
            
            return {
                'symbol': base_symbol,
                'Company_Name': info.get('longName', base_symbol),
                'last_price': ltp if ltp else 0.0,
                'Previous_Close': prev_close,
                'Change': change,
                'Change_Percent': change_pct,
                'Volume': volume,
                'Market_Cap': market_cap,
                'Sector': info.get('sector', 'N/A'),
                'Industry': info.get('industry', 'N/A'),
                'Error': None
            }
            
        except Exception as e:
            return self._get_individual_fallback(symbol)
    
    def _get_individual_fallback(self, symbol):
        """Fallback method for individual stock fetch"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            ltp = info.get('currentPrice') or info.get('regularMarketPrice')
            prev_close = info.get('previousClose', 'N/A')
            
            return {
                'Symbol': symbol.replace('.NS', ''),
                'Company_Name': info.get('longName', symbol.replace('.NS', '')),
                'LTP': ltp if ltp else 'N/A',
                'Previous_Close': prev_close,
                'Change': 'N/A',
                'Change_Percent': 'N/A',
                'Volume': info.get('volume', 'N/A'),
                'Market_Cap': info.get('marketCap', 'N/A'),
                'Sector': info.get('sector', 'N/A'),
                'Industry': info.get('industry', 'N/A'),
                'Error': 'Individual fetch'
            }
        except Exception as e:
            return {
                'Symbol': symbol.replace('.NS', ''),
                'Company_Name': 'N/A',
                'LTP': 'N/A',
                'Previous_Close': 'N/A',
                'Change': 'N/A',
                'Change_Percent': 'N/A',
                'Volume': 'N/A',
                'Market_Cap': 'N/A',
                'Sector': 'N/A',
                'Industry': 'N/A',
                'Error': str(e)
            }
    
    def generate_report(self, df):
        """Generate summary report"""
        successful = len(df[df['LTP'] != 'N/A'])
        total = len(df)
        
        print("\n" + "="*70)
        print("NSE STOCKS DATA REPORT")
        print("="*70)
        print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total stocks processed: {total}")
        print(f"Successfully fetched: {successful}")
        print(f"Failed: {total - successful}")
        print(f"Success rate: {(successful/total)*100:.1f}%")
        
        # Top gainers (if data available)
        if successful > 0:
            valid_data = df[df['Change_Percent'] != 'N/A'].copy()
            if len(valid_data) > 0:
                valid_data['Change_Percent'] = pd.to_numeric(valid_data['Change_Percent'], errors='coerce')
                valid_data = valid_data.dropna(subset=['Change_Percent'])
                
                if len(valid_data) > 0:
                    print(f"\nTop 5 Gainers:")
                    top_gainers = valid_data.nlargest(5, 'Change_Percent')
                    for _, row in top_gainers.iterrows():
                        print(f"  {row['Symbol']}: +{row['Change_Percent']:.2f}%")
                    
                    print(f"\nTop 5 Losers:")
                    top_losers = valid_data.nsmallest(5, 'Change_Percent')
                    for _, row in top_losers.iterrows():
                        print(f"  {row['Symbol']}: {row['Change_Percent']:.2f}%")

# Usage
if __name__ == "__main__":
    nse_data = NSETickersData()
    symbols = nse_data.get_symbols()
    
    print(f"Starting data fetch for {len(symbols)} NSE stocks...")
    start_time = time.time()
    
    results = nse_data.fetch_stock_data(symbols, batch_size=50)

    print(results)
    
    end_time = time.time()
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Generate report
    nse_data.generate_report(df)
    print(df)
    
    # # Save results
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # filename = f"nse_500_data_{timestamp}.csv"
    # df.to_csv(filename, index=False)
    
    # print(f"\nData saved to: {filename}")
    print(f"Total execution time: {end_time - start_time:.2f} seconds")