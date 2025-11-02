import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import io
import requests
import time

# Page config
st.set_page_config(
    page_title="NSE Stock Data Downloader",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("📊 NSE Stock Data Downloader")
st.markdown("Download Indian equity data for DCF analysis with automatic gap filling from NSE")

# Nifty Indices dictionary - Complete list from NSE
nifty_indices = {
    # Broad Market Indices
    'NIFTY 50': '^NSEI',
    'NIFTY NEXT 50': '^NIFTYNXT50',
    'NIFTY 100': '^CNX100',
    'NIFTY 200': '^CNX200',
    'NIFTY 500': '^CNX500',
    'NIFTY MIDCAP 50': '^NSMIDCP',
    'NIFTY MIDCAP 100': '^NIFTY_MIDCAP_100',
    'NIFTY SMALLCAP 100': '^NIFTY_SMLCAP_100',
    
    # Banking & Financial Services
    'NIFTY BANK': '^NSEBANK',
    'NIFTY FINANCIAL SERVICES': '^CNXFINANCE',
    'NIFTY PRIVATE BANK': '^NIFTYPVTBANK',
    'NIFTY PSU BANK': '^CNXPSUBANK',
    'NIFTY FINANCIAL SERVICES 25/50': '^NIFTY_FIN_SERVICE25_50',
    
    # Sectoral Indices
    'NIFTY AUTO': '^CNXAUTO',
    'NIFTY IT': '^CNXIT',
    'NIFTY PHARMA': '^CNXPHARMA',
    'NIFTY FMCG': '^CNXFMCG',
    'NIFTY METAL': '^CNXMETAL',
    'NIFTY REALTY': '^CNXREALTY',
    'NIFTY MEDIA': '^CNXMEDIA',
    'NIFTY HEALTHCARE': '^CNXHEALTH',
    'NIFTY CONSUMER DURABLES': '^CNXCONSUMERDUR',
    'NIFTY OIL & GAS': '^CNXOILGAS',
    
    # Energy & Infrastructure
    'NIFTY ENERGY': '^CNXENERGY',
    'NIFTY INFRASTRUCTURE': '^CNXINFRA',
    'NIFTY PSE': '^CNXPSE',
    
    # Other Sectoral
    'NIFTY CONSUMPTION': '^CNXCONSUMPTION',
    'NIFTY COMMODITIES': '^CNXCOMMODITIES',
    'NIFTY SERVICES SECTOR': '^CNXSERVICE',
    'NIFTY MNC': '^CNXMNC',
}

# NSE API index name mapping (these are the exact names NSE API expects)
nse_api_index_mapping = {
    'NIFTY 50': 'NIFTY 50',
    'NIFTY NEXT 50': 'NIFTY NEXT 50',
    'NIFTY 100': 'NIFTY 100',
    'NIFTY 200': 'NIFTY 200',
    'NIFTY 500': 'NIFTY 500',
    'NIFTY MIDCAP 50': 'NIFTY MIDCAP 50',
    'NIFTY MIDCAP 100': 'NIFTY MIDCAP 100',
    'NIFTY SMALLCAP 100': 'NIFTY SMLCAP 100',
    'NIFTY BANK': 'NIFTY BANK',
    'NIFTY FINANCIAL SERVICES': 'NIFTY FINANCIAL SERVICES',
    'NIFTY PRIVATE BANK': 'NIFTY PRIVATE BANK',
    'NIFTY PSU BANK': 'NIFTY PSU BANK',
    'NIFTY AUTO': 'NIFTY AUTO',
    'NIFTY IT': 'NIFTY IT',
    'NIFTY PHARMA': 'NIFTY PHARMA',
    'NIFTY FMCG': 'NIFTY FMCG',
    'NIFTY METAL': 'NIFTY METAL',
    'NIFTY REALTY': 'NIFTY REALTY',
    'NIFTY MEDIA': 'NIFTY MEDIA',
    'NIFTY ENERGY': 'NIFTY ENERGY',
    'NIFTY INFRASTRUCTURE': 'NIFTY INFRASTRUCTURE',
    'NIFTY PSE': 'NIFTY PSE',
    'NIFTY CONSUMPTION': 'NIFTY CONSUMPTION',
    'NIFTY COMMODITIES': 'NIFTY COMMODITIES',
    'NIFTY OIL & GAS': 'NIFTY OIL AND GAS',
    'NIFTY HEALTHCARE': 'NIFTY HEALTHCARE INDEX',
    'NIFTY CONSUMER DURABLES': 'NIFTY CONSUMER DURABLES',
}

def fetch_nse_index_data(index_name, start_date, end_date):
    """Fetch index data directly from niftyindices.com"""
    try:
        # Nifty Indices API endpoint
        base_url = "https://www.niftyindices.com"
        api_url = 'https://www.niftyindices.com/Backpage.aspx/getHistoricaldatatabletoString'
        
        # Headers to mimic browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json; charset=UTF-8",
            "x-requested-with": "XMLHttpRequest",
            "origin": base_url,
            "referer": f"{base_url}/"
        }
        
        # Create session and get cookies
        session = requests.Session()
        session.get(base_url, headers=headers, timeout=10)
        time.sleep(0.5)
        
        # Format dates as DD-MMM-YYYY (e.g., 01-Jan-2021)
        start_str = start_date.strftime('%d-%b-%Y')
        end_str = end_date.strftime('%d-%b-%Y')
        
        # Payload for API request - exact format from the working example
        payload = {
            'name': index_name,
            'startDate': start_str,
            'endDate': end_str
        }
        
        # Make API request
        response = session.post(api_url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse the response - data comes in 'd' key as JSON string
            if 'd' in data and data['d']:
                # Parse the JSON string inside 'd'
                df = pd.read_json(io.StringIO(data['d']))
                
                if not df.empty and 'HistoricalDate' in df.columns and 'CLOSE' in df.columns:
                    # Convert date column - format is DD-MMM-YYYY
                    df['HistoricalDate'] = pd.to_datetime(df['HistoricalDate'], format='%d-%b-%Y')
                    
                    # Create series with date as index and Close as values
                    result = pd.Series(
                        data=df['CLOSE'].values,
                        index=df['HistoricalDate']
                    )
                    return result
        
        return None
        
    except Exception as e:
        # Silently fail - we'll show aggregate message
        return None

def fetch_nse_stock_data(symbol, start_date, end_date):
    """Fetch stock data from NSE website"""
    try:
        # NSE equity historical data endpoint
        base_url = "https://www.nseindia.com"
        page_url = "https://www.nseindia.com/get-quotes/equity"
        api_url = "https://www.nseindia.com/api/historical/cm/equity"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": page_url,
            "X-Requested-With": "XMLHttpRequest"
        }
        
        # Create session and establish cookies
        session = requests.Session()
        session.get(base_url, headers=headers, timeout=10)
        time.sleep(1)
        
        # Visit the equity page to establish proper session
        session.get(f"{page_url}?symbol={symbol}", headers=headers, timeout=10)
        time.sleep(1)
        
        # Add date range parameters
        params = {
            'symbol': symbol,
            'series': '["EQ"]',
            'from': start_date.strftime('%d-%m-%Y'),
            'to': end_date.strftime('%d-%m-%Y')
        }
        
        response = session.get(api_url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and data['data']:
                df = pd.DataFrame(data['data'])
                df['CH_TIMESTAMP'] = pd.to_datetime(df['CH_TIMESTAMP'], format='%d-%b-%Y')
                
                result = pd.Series(
                    data=df['CH_CLOSING_PRICE'].values,
                    index=df['CH_TIMESTAMP']
                )
                return result
        
        return None
        
    except Exception as e:
        return None

def fill_missing_data_from_nse(df, tickers, selected_indices, start_date, end_date, price_type):
    """Fill missing data using NSE website scraping"""
    
    filled_count = 0
    total_missing = 0
    
    # Get all columns except Date
    data_columns = [col for col in df.columns if col != 'Date']
    
    for col in data_columns:
        # Check if column has missing values
        missing_mask = df[col].isna()
        missing_count = missing_mask.sum()
        
        if missing_count == 0:
            continue
        
        total_missing += missing_count
        st.info(f"🔍 Found {missing_count} missing values in {col}, fetching from NSE...")
        
        # Determine if it's a stock or index
        if col in tickers:
            # It's a stock - fetch from NSE
            try:
                nse_data = fetch_nse_stock_data(col, start_date, end_date)
                if nse_data is not None:
                    for idx in df[missing_mask].index:
                        if idx in nse_data.index:
                            df.loc[idx, col] = nse_data.loc[idx]
                            filled_count += 1
                
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                st.warning(f"Could not fill {col}: {str(e)}")
        
        elif col in selected_indices:
            # It's an index - fetch from Nifty Indices API
            if col in nse_api_index_mapping:
                try:
                    api_index_name = nse_api_index_mapping[col]
                    nse_data = fetch_nse_index_data(api_index_name, start_date, end_date)
                    
                    if nse_data is not None:
                        for idx in df[missing_mask].index:
                            # Normalize the date to remove time component
                            date_only = pd.Timestamp(idx.date())
                            
                            # Try exact match
                            if date_only in nse_data.index:
                                df.loc[idx, col] = nse_data.loc[date_only]
                                filled_count += 1
                    
                    time.sleep(1)  # Rate limiting - NSE is strict
                except Exception as e:
                    st.warning(f"Could not fill {col}: {str(e)}")
            else:
                st.warning(f"⚠️ {col} not supported by NSE API - gaps will remain")
    
    return df, filled_count, total_missing

# Create three columns for better layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎯 Stock Tickers")
    
    tickers_input = st.text_area(
        "Enter stock tickers (one per line, without .NS)",
        placeholder="RELIANCE\nTCS\nINFY\nHDFC",
        height=150,
        help="Enter Indian stock tickers without the .NS suffix"
    )
    
    # Parse tickers
    tickers = [t.strip().upper() for t in tickers_input.split('\n') if t.strip()]

with col2:
    st.subheader("📈 NIFTY Indices")
    
    # Multi-select for indices
    selected_indices = st.multiselect(
        "Select indices to include",
        options=list(nifty_indices.keys()),
        help="Select one or more NIFTY indices"
    )

# Time period section
st.subheader("📅 Time Period")

col3, col4, col5 = st.columns([1, 1, 1])

with col3:
    period_type = st.selectbox(
        "Select Period Type",
        options=['Predefined', 'Custom Date Range']
    )

if period_type == 'Predefined':
    with col4:
        period = st.selectbox(
            "Select Period",
            options=['1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max'],
            index=3,  # Default to 1y
            format_func=lambda x: {
                '1mo': '1 Month',
                '3mo': '3 Months',
                '6mo': '6 Months',
                '1y': '1 Year',
                '2y': '2 Years',
                '5y': '5 Years',
                '10y': '10 Years',
                'max': 'Maximum Available'
            }[x]
        )
    start_date = None
    end_date = None
else:
    with col4:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=365),
            max_value=datetime.now()
        )
    with col5:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            max_value=datetime.now()
        )
    period = None

# Price type selection
st.subheader("💰 Price Type")
price_type = st.selectbox(
    "Select Price Column",
    options=['Close', 'Adj Close', 'Open'],
    index=0,
    help="Close: Actual closing price (matches NSE) | Adj Close: Adjusted for splits/dividends | Open: Opening price"
)

# Gap filling option
st.subheader("🔧 Data Quality")
use_nse_backup = st.checkbox(
    "Auto-fill missing data from NSE website (recommended)",
    value=True,
    help="If Yahoo Finance has gaps, automatically fetch missing data directly from NSE website"
)

# Add some spacing
st.markdown("---")

# Create Dataset button
if st.button("🚀 Create Dataset", type="primary", use_container_width=True):
    
    # Validation
    if not tickers and not selected_indices:
        st.error("⚠️ Please add at least one ticker or select an index")
    elif period_type == 'Custom Date Range' and start_date >= end_date:
        st.error("⚠️ Start date must be before end date")
    else:
        with st.spinner("📡 Fetching data from Yahoo Finance..."):
            try:
                # Prepare symbols
                stock_symbols = [f"{ticker}.NS" for ticker in tickers]
                index_symbols = [nifty_indices[idx] for idx in selected_indices]
                all_symbols = stock_symbols + index_symbols
                
                # Fetch data with auto_adjust=False to get raw unadjusted prices
                if period_type == 'Predefined':
                    data = yf.download(all_symbols, period=period, auto_adjust=False, progress=False)
                else:
                    data = yf.download(
                        all_symbols, 
                        start=start_date, 
                        end=end_date,
                        auto_adjust=False,
                        progress=False
                    )
                
                # Check if data is empty or invalid
                if data.empty:
                    st.error("❌ No data received. Please check the ticker symbols and try again.")
                    st.error("⚠️ Make sure the tickers are valid NSE symbols (e.g., RELIANCE, TCS, INFY)")
                    st.stop()
                
                # Check if any columns have all NaN values (invalid ticker)
                if len(all_symbols) == 1:
                    if data[price_type].isna().all():
                        st.error("❌ Invalid ticker symbol. No data available.")
                        st.error("⚠️ Please verify the ticker symbol is correct and listed on NSE")
                        st.stop()
                else:
                    # For multiple symbols, check if all price data is NaN
                    if isinstance(data.columns, pd.MultiIndex):
                        price_data = data[price_type]
                    else:
                        price_data = data
                    
                    # Check which symbols have no data
                    invalid_symbols = []
                    for symbol in all_symbols:
                        if symbol in price_data.columns and price_data[symbol].isna().all():
                            invalid_symbols.append(symbol)
                    
                    if invalid_symbols:
                        st.error(f"❌ Invalid ticker(s): {', '.join(invalid_symbols)}")
                        st.error("⚠️ Please check the ticker symbols and try again")
                        st.stop()
                
                # Handle single vs multiple tickers
                if len(all_symbols) == 1:
                    df = pd.DataFrame({
                        'Date': data.index,
                        all_symbols[0]: data[price_type].values
                    })
                else:
                    if isinstance(data.columns, pd.MultiIndex):
                        df = data[price_type].copy()
                    else:
                        df = data[[price_type]].copy()
                    df.reset_index(inplace=True)
                
                # Rename columns to remove .NS and use friendly index names
                column_mapping = {'Date': 'Date'}
                for ticker in tickers:
                    column_mapping[f"{ticker}.NS"] = ticker
                for idx_name in selected_indices:
                    column_mapping[nifty_indices[idx_name]] = idx_name
                
                df.rename(columns=column_mapping, inplace=True)
                
                # Reorder columns: Date, then tickers, then indices
                ordered_columns = ['Date'] + tickers + selected_indices
                df = df[ordered_columns]
                
                # Format date as datetime
                df['Date'] = pd.to_datetime(df['Date'])
                
                # Count missing values before filling
                missing_count_yf = df.iloc[:, 1:].isna().sum().sum()
                
                if missing_count_yf > 0:
                    st.warning(f"⚠️ Yahoo Finance data has {missing_count_yf} missing values")
                    
                    # Attempt to fill with NSE scraping if enabled
                    if use_nse_backup:
                        st.info("🔄 Fetching missing data directly from NSE website...")
                        
                        # Determine date range for NSE scraping
                        if period_type == 'Predefined':
                            # Calculate approximate start date based on period
                            period_days = {
                                '1mo': 30, '3mo': 90, '6mo': 180, '1y': 365,
                                '2y': 730, '5y': 1825, '10y': 3650, 'max': 7300
                            }
                            days = period_days.get(period, 365)
                            nse_start = datetime.now() - timedelta(days=days)
                            nse_end = datetime.now()
                        else:
                            nse_start = start_date
                            nse_end = end_date
                        
                        df, filled_count, total_missing = fill_missing_data_from_nse(
                            df, tickers, selected_indices, nse_start, nse_end, price_type
                        )
                        
                        if filled_count > 0:
                            st.success(f"✅ Successfully filled {filled_count} values from NSE website!")
                        
                        remaining_missing = df.iloc[:, 1:].isna().sum().sum()
                        if remaining_missing > 0:
                            st.warning(f"⚠️ {remaining_missing} values still missing (may be market holidays)")
                else:
                    st.success("✅ No missing values in Yahoo Finance data!")
                
                # Round all price columns to 2 decimal places
                for col in df.columns:
                    if col != 'Date':
                        df[col] = df[col].round(2)
                
                # Store in session state
                st.session_state['dataframe'] = df
                st.session_state['symbols'] = tickers + selected_indices
                
                st.success(f"✅ Successfully created dataset with {len(df)} rows!")
                
            except Exception as e:
                st.error(f"❌ Error fetching data: {str(e)}")
                st.error("⚠️ Please check the ticker symbols entered and try again.")

# Display data and download option
if 'dataframe' in st.session_state:
    st.markdown("---")
    st.subheader("📊 Data Preview")
    
    df = st.session_state['dataframe']
    
    # Create display dataframe with formatted dates
    df_display = df.copy()
    df_display['Date'] = df_display['Date'].dt.strftime('%d-%m-%Y')
    
    # Display preview without index
    st.dataframe(df_display.head(10), use_container_width=True, hide_index=True)
    
    if len(df) > 10:
        st.info(f"Showing first 10 of {len(df)} rows")
    
    # Statistics
    st.subheader("📈 Quick Statistics")
    col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
    
    # Count current missing values
    missing_count = df.iloc[:, 1:].isna().sum().sum()
    
    with col_stats1:
        st.metric("Total Rows", len(df))
    with col_stats2:
        st.metric("Missing Values", missing_count)
    with col_stats3:
        st.metric("Start Date", df['Date'].min().strftime('%d-%m-%Y'))
    with col_stats4:
        st.metric("End Date", df['Date'].max().strftime('%d-%m-%Y'))
    
    # Show which columns have missing data
    if missing_count > 0:
        st.markdown("**⚠️ Columns with Missing Data:**")
        missing_by_col = df.iloc[:, 1:].isna().sum()
        missing_by_col = missing_by_col[missing_by_col > 0]
        if not missing_by_col.empty:
            for col, count in missing_by_col.items():
                st.text(f"  • {col}: {count} missing values")
    
    # Download section
    st.markdown("---")
    st.subheader("⬇️ Download Data")
    
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        # Excel download
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_excel = df.copy()
            df_excel.to_excel(writer, index=False, sheet_name='Stock Data')
            
            workbook = writer.book
            worksheet = writer.sheets['Stock Data']
            
            # Format date column
            for row in range(2, len(df_excel) + 2):
                cell = worksheet.cell(row=row, column=1)
                cell.number_format = 'DD-MM-YYYY'
            
            # Format price columns
            for col_idx, col_name in enumerate(df_excel.columns, start=1):
                if col_name != 'Date':
                    for row in range(2, len(df_excel) + 2):
                        cell = worksheet.cell(row=row, column=col_idx)
                        cell.number_format = '0.00'
        
        st.download_button(
            label="📥 Download as Excel",
            data=buffer.getvalue(),
            file_name=f"nse_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col_dl2:
        # CSV download
        df_csv = df.copy()
        df_csv['Date'] = df_csv['Date'].dt.strftime('%d-%m-%Y')
        csv = df_csv.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"nse_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    <p>💡 <strong>Pro Tips:</strong></p>
    <ul style='list-style-type: none; padding: 0;'>
        <li>✓ Hybrid approach: Yahoo Finance (fast) + NSE Website (accurate gap filling)</li>
        <li>✓ Use 'Close' price type to match NSE website prices</li>
        <li>✓ Auto-fill scrapes data directly from niftyindices.com</li>
        <li>✓ Excel files can be directly used in your DCF models</li>
    </ul>
</div>
""", unsafe_allow_html=True)
