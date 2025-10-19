import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import io

# Page config
st.set_page_config(
    page_title="NSE Stock Data Downloader",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("📊 NSE Stock Data Downloader")
st.markdown("Download Indian equity data for DCF analysis")

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
        with st.spinner("Fetching data from Yahoo Finance..."):
            try:
                # Prepare symbols
                stock_symbols = [f"{ticker}.NS" for ticker in tickers]
                index_symbols = [nifty_indices[idx] for idx in selected_indices]
                all_symbols = stock_symbols + index_symbols
                
                # Fetch data
                if period_type == 'Predefined':
                    data = yf.download(all_symbols, period=period, progress=False)
                else:
                    data = yf.download(
                        all_symbols, 
                        start=start_date, 
                        end=end_date,
                        progress=False
                    )
                
                # Check if data is empty
                if data.empty:
                    st.error("⚠️ No data received. Please check the ticker symbols and try again.")
                    st.stop()
                
                # Handle single vs multiple tickers - FIXED to use correct Close price
                if len(all_symbols) == 1:
                    # For single ticker, structure is simple
                    df = pd.DataFrame({
                        'Date': data.index,
                        all_symbols[0]: data[price_type].values
                    })
                else:
                    # For multiple tickers, data has MultiIndex columns
                    # Explicitly extract the selected price type
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
                
                # Format date as dd-mm-yyyy for display but keep as datetime
                df['Date'] = pd.to_datetime(df['Date'])
                
                # Store in session state
                st.session_state['dataframe'] = df
                st.session_state['symbols'] = tickers + selected_indices
                
                st.success(f"✅ Successfully fetched {len(df)} rows of data!")
                
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
    
    with col_stats1:
        st.metric("Total Rows", len(df))
    with col_stats2:
        st.metric("Date Range", f"{(df['Date'].max() - df['Date'].min()).days} days")
    with col_stats3:
        st.metric("Start Date", df['Date'].min().strftime('%d-%m-%Y'))
    with col_stats4:
        st.metric("End Date", df['Date'].max().strftime('%d-%m-%Y'))
    
    # Download section
    st.markdown("---")
    st.subheader("⬇️ Download Data")
    
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        # Excel download - date will be stored as datetime
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Create a copy for Excel with proper date format
            df_excel = df.copy()
            df_excel.to_excel(writer, index=False, sheet_name='Stock Data')
            
            # Format the date column in Excel
            workbook = writer.book
            worksheet = writer.sheets['Stock Data']
            
            # Apply date format to Date column (column A)
            for row in range(2, len(df_excel) + 2):
                cell = worksheet.cell(row=row, column=1)
                cell.number_format = 'DD-MM-YYYY'
        
        st.download_button(
            label="📥 Download as Excel",
            data=buffer.getvalue(),
            file_name=f"nse_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col_dl2:
        # CSV download with formatted dates
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
        <li>✓ No need to add .NS suffix - it's added automatically</li>
        <li>✓ Use 'Close' price type to match NSE website prices</li>
        <li>✓ Data is fetched from Yahoo Finance using yfinance</li>
        <li>✓ Excel files can be directly used in your DCF models</li>
    </ul>
</div>
""", unsafe_allow_html=True)
