import pandas as pd
import requests
from io import StringIO
import time
import yfinance as yf
from datetime import datetime

class NSE500Fetcher:
    """
    A class to fetch the current list of NIFTY 500 stocks.

    It typically scrapes a public index factsheet URL from NSE which contains 
    a link to a downloadable CSV/XLS file. This example uses a known 
    downloadable CSV link for a general index list which is often reliable 
    for fetching symbols.
    """
    def __init__(self):
        # The list of NIFTY 500 constituents is often available as a downloadable
        # CSV file on the NSE website or an index service page.
        # This URL is a common way to fetch an index constituents list, 
        # but *it might change and require updates*.
        self.csv_url = "https://nsearchives.nseindia.com/content/indices/ind_nifty200list.csv"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        self.stock_list = None

    def fetch_df(self):
        """
        Fetches the NIFTY list from the NSE index constituents download URL.

        Returns:
            pandas.DataFrame or None: DataFrame with NIFTY 500 constituents 
                                     if successful, None otherwise.
        """
        print(f"Fetching data from: {self.csv_url}")
        try:
            # Using a requests Session helps maintain state (like cookies) 
            # and is often more successful with NSE's website.
            with requests.Session() as session:
                session.headers.update(self.headers)
                response = session.get(self.csv_url, timeout=15)
                
                # Check for successful response
                response.raise_for_status() 

                # Read the content into a pandas DataFrame
                # Use StringIO to treat the string content as a file
                df  = pd.read_csv(StringIO(response.text))
                
                # Clean up column names for easier access
                df.columns = [col.strip().replace(' ', '_') for col in df.columns]
                return df
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            print("The NSE download link may have changed or network error occurred.")
            return None
        
    def fetch_stock_list(self):
        if self.stock_list is None:
            df = self.fetch_df()
            # Rename specific columns
            rename_map = {
                'Company_Name': 'company_name',
                'Industry': 'industry',
                'Symbol': 'symbol',
                'Series': 'series',
                'ISIN_Code' : 'insin_code'
            }
            df = df.rename(columns=rename_map)
            # Keep only the renamed columns
            df = df[list(rename_map.values())]
            # Convert DataFrame to list of dicts
            stock_list = df.to_dict(orient='records')
            self.stock_list = stock_list
            print(f"Successfully fetched {len(stock_list)} stocks for NIFTY 500.")
            return stock_list
        return stock_list


    def get_symbols_(self):
        """
        Returns a clean list of stock symbols (tickers).

        Returns:
            list or None: List of stock symbols (strings), or None if data 
                          wasn't fetched.
        """
        if self.stock_list is None:
            self.fetch_stock_list()
        
        symbols = [stock['symbol'] for stock in self.stock_list]
        return 
    
    def get_symbols_dot_NS(self, stock_list):
        """
        Returns a clean list of stock symbols (tickers).
        Example: 'RELIANCE.NS', 'TCS.NS',
        Returns:
            list or None: List of stock symbols (strings), or None if data 
                          wasn't fetched.
        """
        
        symbols = [stock['symbol']+".NS" for stock in stock_list]
        return symbols
    
    def get_instrument_list(self):
        """
        Returns a clean list of stock symbols (tickers).

        Returns:
            list or None: List of stock symbols (strings), or None if data 
                          wasn't fetched.
        """
        if self.stock_list is None:
            self.fetch_stock_list()
        
        instruments = ["NSE_EQ|"+stock['insin_code'] for stock in self.stock_list]
        return instruments


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
            success_count = len([r for r in batch_results if r['LTP'] != None])
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
                'LTP': ltp if ltp else 'N/A',
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

# --- Usage Example ---
if __name__ == '__main__':
    # 1. Initialize the fetcher
    nifty500_fetcher = NSE500Fetcher()

    df = nifty500_fetcher.fetch_df()
    print(df)

    # 2. Fetch the data
    nifty500_list = nifty500_fetcher.fetch_stock_list()

    symbols = nifty500_fetcher.get_symbols_dot_NS(nifty500_list)

    print(f"Starting data fetch for {len(symbols)} NSE stocks...")
    start_time = time.time()
    
    results = nifty500_fetcher.fetch_stock_data(symbols, batch_size=200)

    print(results)
    
    end_time = time.time()
    
    print(f"Total execution time: {end_time - start_time:.2f} seconds")

    # 3. Process and display the data
    if nifty500_list is not None:
        print("\n--- First 5 Stocks in NIFTY 500 DataFrame ---")
        print(nifty500_list[:10])
        
        print("\n--- List of all NIFTY 500 Symbols (First 10) ---")
        symbols = nifty500_fetcher.get_symbols()
        if symbols:
            print(symbols[:10])