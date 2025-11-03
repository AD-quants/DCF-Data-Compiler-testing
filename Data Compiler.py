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

async def fetch_nse_data_with_playwright(index_name, target_date):
    """Use Playwright to search Google and get NSE historical data"""
    try:
        async with async_playwright() as p:
            # Launch browser in headless mode
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            # Format date for search query
            date_str = target_date.strftime('%d %B %Y')  # e.g., "01 January 2021"
            
            # Google search query
            search_query = f"NSE {index_name} historical data {date_str}"
            google_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            
            # Go to Google search
            await page.goto(google_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Look for NSE India link in search results
            nse_link = await page.query_selector('a[href*="nseindia.com"]')
            
            if nse_link:
                href = await nse_link.get_attribute('href')
                
                # Visit NSE page
                await page.goto(href, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(3000)
                
                # Try to find the closing price on the page
                # Look for table or price elements
                price_element = await page.query_selector('text=/Close/i')
                
                if price_element:
                    # Try to extract the price near "Close" text
                    parent = await price_element.evaluate('el => el.parentElement')
                    text_content = await page.evaluate('el => el.textContent', parent)
                    
                    # Extract numeric value
                    import re
                    numbers = re.findall(r'[\d,]+\.?\d*', text_content)
                    if numbers:
                        price = float(numbers[0].replace(',', ''))
                        await browser.close()
                        return price
            
            await browser.close()
            return None
            
    except Exception as e:
        return None

def fetch_missing_data_playwright(df, selected_indices, start_date, end_date):
    """Fill missing index data using Playwright browser automation"""
    
    filled_count = 0
    
    # Get all index columns
    index_columns = [col for col in df.columns if col in selected_indices and col != 'Date']
    
    for col in index_columns:
        # Check if column has missing values
        missing_mask = df[col].isna()
        missing_count = missing_mask.sum()
        
        if missing_count == 0:
            continue
        
        st.info(f"🤖 Using browser automation to fetch {missing_count} missing values for {col}...")
        
        # Get missing dates
        missing_dates = df[missing_mask]['Date'].tolist()
        
        # Limit to first 5 missing dates to avoid long wait times
        fetch_dates = missing_dates[:min(5, len(missing_dates))]
        
        for missing_date in fetch_dates:
            try:
                # Use asyncio to run the async function
                price = asyncio.run(fetch_nse_data_with_playwright(col, missing_date))
                
                if price is not None:
                    # Find the row index and fill the value
                    row_idx = df[df['Date'] == missing_date].index[0]
                    df.loc[row_idx, col] = price
                    filled_count += 1
                    st.success(f"✅ Found {col} price for {missing_date.strftime('%d-%m-%Y')}: {price}")
                else:
                    st.warning(f"⚠️ Could not find {col} price for {missing_date.strftime('%d-%m-%Y')}")
                
            except Exception as e:
                st.warning(f"⚠️ Error fetching {col} for {missing_date.strftime('%d-%m-%Y')}: {str(e)}")
        
        if len(missing_dates) > 5:
            st.warning(f"⚠️ Only fetched first 5 of {len(missing_dates)} missing dates to save time")
    
    return df, filled_count
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

# Investing.com index ID mapping for Indian indices
investing_index_mapping = {
    'NIFTY 50': {'id': '40820', 'name': 'nifty-50'},
    'NIFTY BANK': {'id': '40823', 'name': 'nifty-bank'},
    'NIFTY IT': {'id': '40825', 'name': 'nifty-it'},
    'NIFTY PHARMA': {'id': '179881', 'name': 'nifty-pharma'},
    'NIFTY AUTO': {'id': '179875', 'name': 'cnx-auto'},
    'NIFTY FMCG': {'id': '179879', 'name': 'cnx-fmcg'},
    'NIFTY METAL': {'id': '179883', 'name': 'cnx-metal'},
    'NIFTY REALTY': {'id': '179885', 'name': 'cnx-realty'},
    'NIFTY MEDIA': {'id': '179882', 'name': 'cnx-media'},
    'NIFTY ENERGY': {'id': '179878', 'name': 'cnx-energy'},
    'NIFTY FINANCIAL SERVICES': {'id': '40825', 'name': 'nifty-financial'},
    'NIFTY INFRASTRUCTURE': {'id': '179880', 'name': 'cnx-infrastructure'},
    'NIFTY PSE': {'id': '179887', 'name': 'cnx-pse'},
}

def fetch_investing_index_data(index_id, index_name, start_date, end_date):
    """Fetch index data using investpy library"""
    try:
        import investpy
        
        # investpy uses different naming - map to their format
        investpy_name_mapping = {
            'cnx-fmcg': 'Nifty FMCG',
            'nifty-50': 'Nifty 50',
            'nifty-bank': 'Nifty Bank',
            'nifty-it': 'Nifty IT',
            'cnx-pharma': 'Nifty Pharma',
            'cnx-auto': 'Nifty Auto',
            'cnx-metal': 'Nifty Metal',
            'cnx-realty': 'Nifty Realty',
            'cnx-media': 'Nifty Media',
            'cnx-energy': 'Nifty Energy',
            'nifty-financial': 'Nifty Financial Services',
            'cnx-infrastructure': 'Nifty Infrastructure',
            'cnx-pse': 'Nifty PSE',
        }
        
        investpy_index_name = investpy_name_mapping.get(index_name)
        
        if not investpy_index_name:
            return None
        
        # Format dates as DD/MM/YYYY for investpy
        start_str = start_date.strftime('%d/%m/%Y')
        end_str = end_date.strftime('%d/%m/%Y')
        
        # Fetch data using investpy
        df = investpy.get_index_historical_data(
            index=investpy_index_name,
            country='india',
            from_date=start_str,
            to_date=end_str
        )
        
        if not df.empty and 'Close' in df.columns:
            # investpy returns dataframe with date as index
            result = df['Close']
            st.success(f"✅ Fetched {len(result)} records from Investing.com for {investpy_index_name}")
            return result
        
        return None
        
    except Exception as e:
        st.warning(f"⚠️ investpy error for {index_name}: {str(e)}")
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
        time.sleep(0.5)
        
        # Visit the equity page to establish proper session
        session.get(f"{page_url}?symbol={symbol}", headers=headers, timeout=10)
        time.sleep(0.5)
        
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

def fill_missing_data_from_investing(df, tickers, selected_indices, start_date, end_date, price_type):
    """Fill missing data using Investing.com scraping"""
    
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
        st.info(f"🔍 Found {missing_count} missing values in {col}, fetching from Investing.com...")
        
        # Determine if it's a stock or index
        if col in tickers:
            # It's a stock - try NSE first
            try:
                nse_data = fetch_nse_stock_data(col, start_date, end_date)
                if nse_data is not None:
                    for idx in df[missing_mask].index:
                        if idx in nse_data.index:
                            df.loc[idx, col] = nse_data.loc[idx]
                            filled_count += 1
                
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                pass
        
        elif col in selected_indices:
            # It's an index - fetch from Investing.com
            if col in investing_index_mapping:
                try:
                    index_info = investing_index_mapping[col]
                    investing_data = fetch_investing_index_data(
                        index_info['id'], 
                        index_info['name'], 
                        start_date, 
                        end_date
                    )
                    
                    if investing_data is not None:
                        for idx in df[missing_mask].index:
                            # Normalize the date to remove time component
                            date_only = pd.Timestamp(idx.date())
                            
                            # Try exact match
                            if date_only in investing_data.index:
                                df.loc[idx, col] = investing_data.loc[date_only]
                                filled_count += 1
                    
                    time.sleep(0.5)  # Rate limiting
                except Exception as e:
                    pass
            else:
                st.warning(f"⚠️ {col} not available on Investing.com - gaps will remain")
    
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
col_gf1, col_gf2 = st.columns(2)

with col_gf1:
    use_playwright = st.checkbox(
        "Auto-fill using browser automation (Playwright)",
        value=True,
        help="Uses real browser to search Google and get NSE data - slower but reliable"
    )

with col_gf2:
    if use_playwright:
        st.info("🤖 Browser will search Google for missing data")
    else:
        st.info("ℹ️ Missing values will be left blank")

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
                
                # Count missing values before handling
                missing_count_before = df.iloc[:, 1:].isna().sum().sum()
                
                if missing_count_before > 0:
                    st.warning(f"⚠️ Yahoo Finance data has {missing_count_before} missing values")
                    
                    # Use Playwright if enabled
                    if use_playwright:
                        st.info("🤖 Starting browser automation to fetch missing data...")
                        
                        df, filled_count = fetch_missing_data_playwright(
                            df, selected_indices, 
                            df['Date'].min(), df['Date'].max()
                        )
                        
                        if filled_count > 0:
                            st.success(f"✅ Successfully filled {filled_count} values using browser automation!")
                        
                        remaining_missing = df.iloc[:, 1:].isna().sum().sum()
                        if remaining_missing > 0:
                            st.warning(f"⚠️ {remaining_missing} values still missing")
                    else:
                        st.info("ℹ️ Keeping missing values blank for manual review")
                
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
        <li>✓ Data source: Yahoo Finance (fast and reliable)</li>
        <li>✓ Browser automation: Playwright searches Google for missing data</li>
        <li>✓ Use 'Close' price type to match NSE website prices</li>
        <li>✓ Excel files can be directly used in your DCF models</li>
    </ul>
</div>
""", unsafe_allow_html=True)
