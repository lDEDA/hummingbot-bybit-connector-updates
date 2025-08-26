import requests
import pandas as pd
import time
import hmac
import hashlib
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FundingArbitrageAnalyzer:
    def __init__(self, hyperliquid_address: str, bybit_api_key: str, bybit_api_secret: str):
        self.hl_address = hyperliquid_address
        self.bb_api_key = bybit_api_key
        self.bb_api_secret = bybit_api_secret
        self.bb_base_url = "https://api.bybit.com"
        self.bb_recv_window = 5000  # Bybit recommended recv window
    
    def _bb_signed_request(self, endpoint: str, params: dict):
        """Make signed Bybit request"""
        timestamp = str(int(time.time() * 1000))
        
        # Prepare the request to get the exact query string
        req = requests.Request("GET", f"{self.bb_base_url}{endpoint}", params=params)
        prepared = requests.Session().prepare_request(req)
        
        # Extract the raw query string from the prepared request
        if '?' in prepared.path_url:
            raw_query_string = prepared.path_url.split("?", 1)[1]
        else:
            raw_query_string = ""
        
        # Create signature string according to Bybit docs
        sign_str = f"{timestamp}{self.bb_api_key}{self.bb_recv_window}{raw_query_string}"
        signature = hmac.new(
            self.bb_api_secret.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'X-BAPI-API-KEY': self.bb_api_key,
            'X-BAPI-TIMESTAMP': timestamp,
            'X-BAPI-RECV-WINDOW': str(self.bb_recv_window),
            'X-BAPI-SIGN': signature
        }
        
        response = requests.get(f"{self.bb_base_url}{endpoint}", params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('retCode') == 0:
                return data.get('result', {})
            else:
                logger.error(f"Bybit API error: {data.get('retCode')} - {data.get('retMsg')}")
                return {}
        else:
            logger.error(f"Bybit HTTP error: {response.status_code} - {response.text}")
            return {}
    
    def _parse_datetime_string(self, date_str: str, time_str: str = None):
        """Parse date and optional time string to datetime object"""
        if time_str:
            datetime_str = f"{date_str} {time_str}"
            return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        else:
            return datetime.strptime(date_str, "%Y-%m-%d")
    
    def extract_hyperliquid_trades(self, start_datetime: datetime, end_datetime: datetime):
        """Extract Hyperliquid trades within date range"""
        logger.info(f"🔥 Extracting Hyperliquid trades from {start_datetime} to {end_datetime}")
        
        start_timestamp = int(start_datetime.timestamp() * 1000)
        end_timestamp = int(end_datetime.timestamp() * 1000)
        
        trade_data = []
        seen_trades = set()
        batch_size_ms = 24 * 60 * 60 * 1000  # 1 day in milliseconds
        next_start = start_timestamp
        
        while next_start < end_timestamp:
            batch_end = min(next_start + batch_size_ms, end_timestamp)
            
            payload = {
                "type": "userFills",
                "user": self.hl_address,
                "startTime": next_start,
                "endTime": batch_end
            }
            
            response = requests.post("https://api.hyperliquid.xyz/info", json=payload)
            if response.status_code != 200:
                logger.warning(f"❌ Request failed with status {response.status_code}")
                break
            
            batch = response.json()
            if not batch:
                next_start = batch_end + 1
                continue
            
            for fill in batch:
                trade_id = f"{fill.get('time', 0)}_{fill.get('coin', '')}_{fill.get('px', 0)}_{fill.get('sz', 0)}_{fill.get('dir', '')}"
                
                if trade_id not in seen_trades:
                    seen_trades.add(trade_id)
                    trade_data.append({
                        'time': datetime.fromtimestamp(fill.get('time', 0) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                        'coin': fill.get('coin', ''),
                        'dir': fill.get('dir', ''),
                        'px': float(fill.get('px', 0)),
                        'sz': float(fill.get('sz', 0)),
                        'ntl': float(fill.get('sz', 0)) * float(fill.get('px', 0)),
                        'fee': float(fill.get('fee', 0)),
                        'closedPnl': float(fill.get('closedPnl', 0))
                    })
            
            next_start = batch_end + 1
            time.sleep(0.2)
        
        df = pd.DataFrame(trade_data)
        
        # Additional client-side filtering to ensure date range compliance
        if len(df) > 0:
            df['datetime'] = pd.to_datetime(df['time'])
            start_dt = pd.to_datetime(start_datetime)
            end_dt = pd.to_datetime(end_datetime)
            
            # Filter out trades outside the specified date range
            before_filter = len(df)
            df = df[(df['datetime'] >= start_dt) & (df['datetime'] <= end_dt)]
            after_filter = len(df)
            
            if before_filter != after_filter:
                logger.info(f"⚠️  Filtered out {before_filter - after_filter} trades outside date range")
            
            # Remove the temporary datetime column
            df = df.drop('datetime', axis=1)
        
        logger.info(f"✅ Extracted {len(df)} Hyperliquid trades")
        return df
    
    def extract_hyperliquid_funding(self, start_datetime: datetime, end_datetime: datetime):
        """Extract Hyperliquid funding within date range"""
        logger.info(f"🔥 Extracting Hyperliquid funding from {start_datetime} to {end_datetime}")
        
        start_timestamp = int(start_datetime.timestamp() * 1000)
        end_timestamp = int(end_datetime.timestamp() * 1000)
        
        funding_data = []
        seen_funding = set()
        batch_size_ms = 24 * 60 * 60 * 1000
        next_start = start_timestamp
        
        while next_start < end_timestamp:
            batch_end = min(next_start + batch_size_ms, end_timestamp)
            
            payload = {
                "type": "userFunding",
                "user": self.hl_address,
                "startTime": next_start,
                "endTime": batch_end
            }
            
            response = requests.post("https://api.hyperliquid.xyz/info", json=payload)
            if response.status_code != 200:
                logger.warning(f"❌ Request failed with status {response.status_code}")
                break
            
            batch = response.json()
            if not batch:
                next_start = batch_end + 1
                continue
            
            for fund in batch:
                delta = fund.get('delta', {})
                funding_id = f"{fund.get('time', 0)}_{delta.get('coin', '')}_{delta.get('szi', 0)}_{delta.get('usdc', 0)}"
                
                if funding_id not in seen_funding:
                    seen_funding.add(funding_id)
                    funding_data.append({
                        'time': datetime.fromtimestamp(fund.get('time', 0) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                        'coin': delta.get('coin', ''),
                        'sz': float(delta.get('szi', 0)),
                        'side': 'Long' if float(delta.get('szi', 0)) > 0 else 'Short',
                        'payment': float(delta.get('usdc', 0)),
                        'rate': float(delta.get('fundingRate', 0))
                    })
            
            next_start = batch_end + 1
            time.sleep(0.2)
        
        df = pd.DataFrame(funding_data)
        
        # Additional client-side filtering to ensure date range compliance
        if len(df) > 0:
            df['datetime'] = pd.to_datetime(df['time'])
            start_dt = pd.to_datetime(start_datetime)
            end_dt = pd.to_datetime(end_datetime)
            
            # Filter out funding outside the specified date range
            before_filter = len(df)
            df = df[(df['datetime'] >= start_dt) & (df['datetime'] <= end_dt)]
            after_filter = len(df)
            
            if before_filter != after_filter:
                logger.info(f"⚠️  Filtered out {before_filter - after_filter} funding records outside date range")
            
            # Remove the temporary datetime column
            df = df.drop('datetime', axis=1)
        
        logger.info(f"✅ Extracted {len(df)} Hyperliquid funding records")
        return df
    
    def extract_bybit_data(self, start_datetime: datetime, end_datetime: datetime):
        """Extract Bybit data within date range"""
        logger.info(f"🔥 Extracting Bybit data from {start_datetime} to {end_datetime}")
        
        start_timestamp = int(start_datetime.timestamp() * 1000)
        end_timestamp = int(end_datetime.timestamp() * 1000)
        
        combined_data = []
        
        # Bybit limits: 7 days per request, so we need to chunk
        seven_days_ms = 7 * 24 * 60 * 60 * 1000
        
        # First, get list of all executed orders to find symbols
        symbols = set()
        current_start = start_timestamp
        
        while current_start < end_timestamp:
            current_end = min(current_start + seven_days_ms, end_timestamp)
            
            # Get execution list for linear perpetuals
            params = {
                'category': 'linear',
                'startTime': str(current_start),
                'endTime': str(current_end),
                'limit': '100'
            }
            
            cursor = None
            while True:
                if cursor:
                    params['cursor'] = cursor
                
                result = self._bb_signed_request("/v5/execution/list", params)
                if not result:
                    break
                
                executions = result.get('list', [])
                for exec in executions:
                    symbols.add(exec.get('symbol', ''))
                
                cursor = result.get('nextPageCursor')
                if not cursor:
                    break
                time.sleep(0.1)
            
            current_start = current_end + 1
        
        logger.info(f"Found {len(symbols)} unique symbols with trades")
        
        # Now get detailed data for each symbol
        for symbol in symbols:
            if not symbol:
                continue
            
            # Get trades
            current_start = start_timestamp
            while current_start < end_timestamp:
                current_end = min(current_start + seven_days_ms, end_timestamp)
                
                params = {
                    'category': 'linear',
                    'symbol': symbol,
                    'startTime': str(current_start),
                    'endTime': str(current_end),
                    'limit': '100'
                }
                
                cursor = None
                while True:
                    if cursor:
                        params['cursor'] = cursor
                    
                    result = self._bb_signed_request("/v5/execution/list", params)
                    if not result:
                        break
                    
                    executions = result.get('list', [])
                    for exec in executions:
                        exec_type = exec.get('execType', '')
                        
                        if exec_type == 'Funding':
                            # Funding fee record
                            combined_data.append({
                                'type': 'FUNDING_FEE',
                                'time': datetime.fromtimestamp(int(exec.get('execTime', 0)) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                                'symbol': exec.get('symbol', ''),
                                'amount': -float(exec.get('execFee', 0)),  # Make negative (Bybit returns positive for fees paid)
                                'asset': 'USDT',
                                'tranId': exec.get('execId', ''),
                                'tradeId': '',
                                'side': '',
                                'quantity': '',
                                'price': '',
                                'realizedPnl': ''
                            })
                        else:
                            # Trade record
                            combined_data.append({
                                'type': 'TRADE',
                                'time': datetime.fromtimestamp(int(exec.get('execTime', 0)) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                                'symbol': exec.get('symbol', ''),
                                'amount': abs(float(exec.get('execFee', 0))),  # Commission (always positive)
                                'asset': 'USDT',
                                'tranId': exec.get('execId', ''),
                                'tradeId': exec.get('orderId', ''),
                                'side': exec.get('side', ''),
                                'quantity': float(exec.get('execQty', 0)),
                                'price': float(exec.get('execPrice', 0)),
                                'realizedPnl': float(exec.get('closedPnl', 0)) if exec.get('closedPnl') else 0
                            })
                    
                    cursor = result.get('nextPageCursor')
                    if not cursor:
                        break
                    time.sleep(0.1)
                
                current_start = current_end + 1
                time.sleep(0.2)
        
        # Also get closed PnL records
        current_start = start_timestamp
        while current_start < end_timestamp:
            current_end = min(current_start + seven_days_ms, end_timestamp)
            
            params = {
                'category': 'linear',
                'startTime': str(current_start),
                'endTime': str(current_end),
                'limit': '100'
            }
            
            cursor = None
            while True:
                if cursor:
                    params['cursor'] = cursor
                
                result = self._bb_signed_request("/v5/position/closed-pnl", params)
                if not result:
                    break
                
                pnl_records = result.get('list', [])
                for pnl in pnl_records:
                    # Add closed PnL as commission record (for tracking purposes)
                    combined_data.append({
                        'type': 'COMMISSION',
                        'time': datetime.fromtimestamp(int(pnl.get('updatedTime', 0)) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                        'symbol': pnl.get('symbol', ''),
                        'amount': 0,  # No commission on PnL record
                        'asset': 'USDT',
                        'tranId': pnl.get('orderId', ''),
                        'tradeId': pnl.get('orderId', ''),
                        'side': pnl.get('side', ''),
                        'quantity': float(pnl.get('qty', 0)),
                        'price': float(pnl.get('avgEntryPrice', 0)),
                        'realizedPnl': float(pnl.get('closedPnl', 0))
                    })
                
                cursor = result.get('nextPageCursor')
                if not cursor:
                    break
                time.sleep(0.1)
            
            current_start = current_end + 1
        
        df = pd.DataFrame(combined_data)
        if len(df) > 0:
            df = df.sort_values('time')
        
        logger.info(f"✅ Extracted {len(df)} Bybit records")
        return df
    
    def analyze_performance(self, start_date: str, start_time: str, end_date: str, end_time: str, target_coins: list = None):
        """Analyze funding arbitrage performance for specific date/time range"""
        
        # Parse start and end datetime
        start_datetime = self._parse_datetime_string(start_date, start_time)
        end_datetime = self._parse_datetime_string(end_date, end_time)
        
        logger.info(f"🎯 Analyzing performance from {start_datetime} to {end_datetime}")
        
        # Default target coins if not specified
        if target_coins is None:
            target_coins = ['DOGE', 'ARB', 'ENA', 'NEIROETH', 'MOODENG', 'FARTCOIN', 'IP', 'HYPE', 'RESOLV', 'PUMP']
        
        # Extract data for the specified period
        hl_trades_df_raw = self.extract_hyperliquid_trades(start_datetime, end_datetime)
        hl_funding_df_raw = self.extract_hyperliquid_funding(start_datetime, end_datetime)
        bb_combined_df_raw = self.extract_bybit_data(start_datetime, end_datetime)
        
        # Debug: Check actual date ranges in extracted data
        if len(hl_trades_df_raw) > 0:
            logger.info(f"📊 HL Trades date range: {hl_trades_df_raw['time'].min()} to {hl_trades_df_raw['time'].max()}")
            logger.info(f"📊 HL Trades total records: {len(hl_trades_df_raw)}")
        if len(hl_funding_df_raw) > 0:
            logger.info(f"📊 HL Funding date range: {hl_funding_df_raw['time'].min()} to {hl_funding_df_raw['time'].max()}")
            logger.info(f"📊 HL Funding total records: {len(hl_funding_df_raw)}")
        if len(bb_combined_df_raw) > 0:
            logger.info(f"📊 BB Data date range: {bb_combined_df_raw['time'].min()} to {bb_combined_df_raw['time'].max()}")
            logger.info(f"📊 BB Data total records: {len(bb_combined_df_raw)}")
        
        # Filter for target coins (for analysis)
        if len(hl_trades_df_raw) > 0:
            hl_trades_df = hl_trades_df_raw[hl_trades_df_raw['coin'].isin(target_coins)]
        else:
            hl_trades_df = hl_trades_df_raw
            
        if len(hl_funding_df_raw) > 0:
            hl_funding_df = hl_funding_df_raw[hl_funding_df_raw['coin'].isin(target_coins)]
        else:
            hl_funding_df = hl_funding_df_raw
        
        target_bb_symbols = [coin + 'USDT' for coin in target_coins]
        if len(bb_combined_df_raw) > 0:
            bb_combined_df = bb_combined_df_raw[bb_combined_df_raw['symbol'].isin(target_bb_symbols)]
        else:
            bb_combined_df = bb_combined_df_raw
        
        # Debug: Check filtered data
        logger.info(f"📊 After filtering for target coins:")
        logger.info(f"📊 HL Trades: {len(hl_trades_df)} records")
        logger.info(f"📊 HL Funding: {len(hl_funding_df)} records") 
        logger.info(f"📊 BB Data: {len(bb_combined_df)} records")
        
        # Convert time columns to datetime
        if len(hl_trades_df) > 0:
            hl_trades_df['datetime'] = pd.to_datetime(hl_trades_df['time'])
        if len(hl_funding_df) > 0:
            hl_funding_df['datetime'] = pd.to_datetime(hl_funding_df['time'])
        if len(bb_combined_df) > 0:
            bb_combined_df['datetime'] = pd.to_datetime(bb_combined_df['time'])
        
        logger.info(f"📊 Filtered data: {len(hl_trades_df)} HL trades, {len(hl_funding_df)} HL funding, {len(bb_combined_df)} BB records")
        
        # Analyze each coin
        analysis_results = []
        
        for coin in target_coins:
            logger.info(f"\n📊 Analyzing {coin}...")
            
            # Get coin-specific data
            if len(hl_trades_df) > 0 and 'coin' in hl_trades_df.columns:
                coin_hl_trades = hl_trades_df[hl_trades_df['coin'] == coin].copy()
            else:
                coin_hl_trades = pd.DataFrame()
                
            if len(hl_funding_df) > 0 and 'coin' in hl_funding_df.columns:
                coin_hl_funding = hl_funding_df[hl_funding_df['coin'] == coin].copy()
            else:
                coin_hl_funding = pd.DataFrame()
                
            if len(bb_combined_df) > 0 and 'symbol' in bb_combined_df.columns:
                coin_bb_data = bb_combined_df[bb_combined_df['symbol'] == coin + 'USDT'].copy()
            else:
                coin_bb_data = pd.DataFrame()
            
            if len(coin_hl_trades) == 0 and len(coin_hl_funding) == 0 and len(coin_bb_data) == 0:
                logger.info(f"  No data found for {coin}")
                continue
            
            # Calculate net position size to determine open/close status
            net_position_size = 0
            position_side = ""
            position_opened = False
            position_closed = False
            
            if len(coin_hl_trades) > 0:
                # Calculate net position: sum all trade sizes with proper signs
                for _, trade in coin_hl_trades.iterrows():
                    trade_size = float(trade['sz'])
                    trade_dir = str(trade['dir']).lower()
                    
                    # Determine sign based on trade direction
                    if 'open' in trade_dir:
                        position_opened = True
                        if 'long' in trade_dir or 'buy' in trade_dir:
                            net_position_size += trade_size  # Long open = positive
                        elif 'short' in trade_dir or 'sell' in trade_dir:
                            net_position_size -= trade_size  # Short open = negative
                    elif 'close' in trade_dir:
                        position_closed = True
                        if 'long' in trade_dir or 'buy' in trade_dir:
                            net_position_size -= trade_size  # Close long = negative
                        elif 'short' in trade_dir or 'sell' in trade_dir:
                            net_position_size += trade_size  # Close short = positive
                
                # Determine position status and side from net size
                if abs(net_position_size) > 0.001:  # Position is open
                    position_is_open = True
                    if net_position_size > 0:
                        position_side = "Long hl"
                    else:
                        position_side = "Short hl"
                else:  # Position is closed (net size ~= 0)
                    position_is_open = False
                    # For closed positions, determine side from the largest absolute trade
                    largest_trade = coin_hl_trades.loc[coin_hl_trades['sz'].abs().idxmax()]
                    if 'long' in str(largest_trade['dir']).lower():
                        position_side = "Long hl (closed)"
                    else:
                        position_side = "Short hl (closed)"
                
                # Debug: Log net position calculation
                logger.info(f"  {coin} Net Position Logic:")
                logger.info(f"    Net position size: {net_position_size:.6f}")
                logger.info(f"    Position is open: {position_is_open}")
                logger.info(f"    Position side: {position_side}")
            else:
                # No trades, check funding to infer position
                position_is_open = True  # Default to open if no trades
                if len(coin_hl_funding) > 0:
                    latest_funding = coin_hl_funding.iloc[-1]
                    if latest_funding['sz'] > 0:
                        position_side = "Long hl"
                    else:
                        position_side = "Short hl"
            
            # Calculate entry and exit prices using new logic
            entry_price = ""
            exit_price = ""
            position_size = abs(net_position_size) if len(coin_hl_trades) > 0 else 0
            
            if position_opened and len(coin_hl_trades) > 0:
                # Get open trades for entry price calculation
                open_trades = coin_hl_trades[coin_hl_trades['dir'].str.contains('Open', case=False, na=False)]
                if len(open_trades) > 0:
                    # Use weighted average price for entry
                    total_size = abs(open_trades['sz'].sum())
                    if total_size > 0:
                        total_notional = (open_trades['sz'].abs() * open_trades['px']).sum()
                        entry_price = total_notional / total_size
            
            # Only show exit price if position is actually closed
            if position_closed and not position_is_open and len(coin_hl_trades) > 0:
                # Get close trades for exit price calculation
                close_trades = coin_hl_trades[coin_hl_trades['dir'].str.contains('Close', case=False, na=False)]
                if len(close_trades) > 0:
                    # Use weighted average price for exit
                    total_size = abs(close_trades['sz'].sum())
                    if total_size > 0:
                        total_notional = (close_trades['sz'].abs() * close_trades['px']).sum()
                        exit_price = total_notional / total_size
            
            # Calculate commissions
            hl_commission_open = 0
            hl_commission_close = 0
            
            if position_is_open:
                # Position is still open - all HL fees are open commissions
                if len(coin_hl_trades) > 0:
                    # Hyperliquid fees are positive, make them negative (costs)
                    hl_commission_open = -coin_hl_trades['fee'].sum()
            else:
                # Position was closed - split HL fees between open and close trades
                if len(open_trades) > 0:
                    # Hyperliquid fees are positive, make them negative (costs)
                    hl_commission_open = -open_trades['fee'].sum()
                if len(close_trades) > 0:
                    # Hyperliquid fees are positive, make them negative (costs)
                    hl_commission_close = -close_trades['fee'].sum()
            
            # For Bybit: ALL commissions are treated as open commissions
            bb_trades = coin_bb_data[coin_bb_data['type'] == 'TRADE']
            bb_commission_open = 0
            bb_commission_close = 0
            
            if len(bb_trades) > 0:
                # Bybit fees are already negative in the data
                bb_commission_open = -abs(bb_trades['amount'].sum())
                # Debug: Log commission details
                logger.info(f"  {coin} BB commission details:")
                logger.info(f"    BB trade records: {len(bb_trades)} (total: {bb_commission_open:.6f})")
                if len(bb_trades) > 0:
                    logger.info(f"    BB trade date range: {bb_trades['time'].min()} to {bb_trades['time'].max()}")
            
            total_commission_open = hl_commission_open + bb_commission_open
            total_commission_close = hl_commission_close
            
            # Calculate funding
            hl_funding_total = coin_hl_funding['payment'].sum() if len(coin_hl_funding) > 0 else 0
            bb_funding_total = coin_bb_data[coin_bb_data['type'] == 'FUNDING_FEE']['amount'].sum() if len(coin_bb_data) > 0 else 0
            total_funding = hl_funding_total + bb_funding_total
            
            # Debug: Log funding calculation details
            if len(coin_hl_funding) > 0 or bb_funding_total != 0:
                logger.info(f"  {coin} funding details:")
                logger.info(f"    HL funding records: {len(coin_hl_funding)} (total: {hl_funding_total:.6f})")
                logger.info(f"    BB funding total: {bb_funding_total:.6f}")
                if len(coin_hl_funding) > 0:
                    logger.info(f"    HL funding date range: {coin_hl_funding['time'].min()} to {coin_hl_funding['time'].max()}")
                bb_funding_records = coin_bb_data[coin_bb_data['type'] == 'FUNDING_FEE']
                if len(bb_funding_records) > 0:
                    logger.info(f"    BB funding records: {len(bb_funding_records)}")
                    logger.info(f"    BB funding date range: {bb_funding_records['time'].min()} to {bb_funding_records['time'].max()}")
            
            # Calculate total PnL
            realized_pnl = total_commission_open + total_commission_close + total_funding
            
            # Calculate percentage and APR
            if coin in ['LINK', 'LTC']:
                percentage = (realized_pnl / 40) * 100
            else:
                percentage = (realized_pnl / 20) * 100
            
            # Calculate duration and APR using specified analysis period
            duration = end_datetime - start_datetime
            duration_hours = duration.total_seconds() / 3600
            
            # Calculate APR based on the specified analysis period
            apr = 0
            if duration_hours > 0 and percentage != 0:
                apr = (percentage / duration_hours) * (365 * 24)  # Annualize
            
            # Calculate APR excluding commissions (funding only)
            funding_only_pnl = total_funding
            if coin in ['LINK', 'LTC']:
                funding_percentage = (funding_only_pnl / 40) * 100
            else:
                funding_percentage = (funding_only_pnl / 20) * 100
            
            apr_excluding_commission = 0
            if duration_hours > 0 and funding_percentage != 0:
                apr_excluding_commission = (funding_percentage / duration_hours) * (365 * 24)
            
            # Calculate how many days it took for commission to be paid
            total_commission_cost = abs(total_commission_open + total_commission_close)
            days_until_commission_paid = 999999  # Default large number
            
            if total_commission_cost > 0 and total_funding > 0:
                if total_funding >= total_commission_cost:
                    # Funding has already covered commission costs
                    funding_per_hour = total_funding / duration_hours if duration_hours > 0 else 0
                    if funding_per_hour > 0:
                        hours_to_cover = total_commission_cost / funding_per_hour
                        days_until_commission_paid = hours_to_cover / 24
                    else:
                        days_until_commission_paid = 0
                else:
                    # Funding is positive but hasn't covered commission yet
                    funding_per_hour = total_funding / duration_hours if duration_hours > 0 else 0
                    if funding_per_hour > 0:
                        hours_to_cover = total_commission_cost / funding_per_hour
                        days_until_commission_paid = hours_to_cover / 24
                    else:
                        days_until_commission_paid = 999999
            elif total_commission_cost > 0 and total_funding <= 0:
                # Funding is negative or zero, set to large number
                days_until_commission_paid = 999999
            elif total_commission_cost == 0:
                # No commission costs, set to 0
                days_until_commission_paid = 0
            
            logger.info(f"  Position: {position_side}")
            logger.info(f"  Entry: {entry_price}, Exit: {exit_price}")
            logger.info(f"  Size: {position_size}")
            logger.info(f"  Commission Open: {total_commission_open:.6f}, Close: {total_commission_close:.6f}")
            logger.info(f"  Funding: {total_funding:.6f}")
            logger.info(f"  Realized PnL: {realized_pnl:.6f}")
            logger.info(f"  Percentage: {percentage:.4f}%")
            logger.info(f"  Duration: {duration_hours:.2f} hours")
            logger.info(f"  APR: {apr:.4f}%")
            logger.info(f"  APR (excluding commission): {apr_excluding_commission:.4f}%")
            logger.info(f"  Days until commission paid: {days_until_commission_paid:.2f}")
            
            analysis_results.append({
                'Symbol': coin,
                'Side': position_side,
                'Entry Price': entry_price if entry_price != "" else "",
                'Exit Price': exit_price if exit_price != "" else "",
                'Position Size': position_size,
                'Commission (Open)': total_commission_open,
                'Commission (Close)': total_commission_close,
                'Funding Paid/Received': total_funding,
                'Realized PnL': realized_pnl,
                'Percentage': percentage,
                'Duration (hours)': duration_hours,
                'APR': apr,
                'APR (excluding commission)': apr_excluding_commission,
                'Days until commission paid': days_until_commission_paid
            })
        
        # Create results DataFrame
        results_df = pd.DataFrame(analysis_results)
        
        # Create Excel file with 4 sheets
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_filename = f"funding_arbitrage_analysis_bybit_{timestamp}.xlsx"
        csv_filename = f"funding_arbitrage_analysis_bybit_{timestamp}.csv"
        
        try:
            import openpyxl
            
            with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
                # Sheet 1: Analysis Summary
                results_df.to_excel(writer, sheet_name='Analysis_Summary', index=False)
                logger.info(f"✅ Added Analysis Summary sheet ({len(results_df)} rows)")
                
                # Sheet 2: Hyperliquid Trades (filtered by date range AND target coins)
                hl_trades_df.to_excel(writer, sheet_name='Hyperliquid_Trades', index=False)
                logger.info(f"✅ Added Hyperliquid Trades sheet ({len(hl_trades_df)} rows)")
                
                # Sheet 3: Hyperliquid Funding (filtered by date range AND target coins)
                hl_funding_df.to_excel(writer, sheet_name='Hyperliquid_Funding', index=False)
                logger.info(f"✅ Added Hyperliquid Funding sheet ({len(hl_funding_df)} rows)")
                
                # Sheet 4: Bybit Data (filtered by date range AND target coins)
                bb_combined_df.to_excel(writer, sheet_name='Bybit_Data', index=False)
                logger.info(f"✅ Added Bybit Data sheet ({len(bb_combined_df)} rows)")
            
            logger.info(f"\n✅ Excel file created: {excel_filename}")
            
        except ImportError:
            logger.warning("⚠️  openpyxl not installed. Install with: pip install openpyxl")
            logger.info("Creating CSV file instead...")
        
        # Also save CSV for compatibility
        results_df.to_csv(csv_filename, index=False)
        logger.info(f"✅ CSV file created: {csv_filename}")
        
        logger.info(f"\n📊 SUMMARY ({start_datetime} to {end_datetime}):")
        print(results_df.to_string(index=False))
        
        # Calculate totals
        if len(results_df) > 0:
            total_pnl = results_df['Realized PnL'].sum()
            total_commission_open_sum = results_df['Commission (Open)'].sum()
            total_commission_close_sum = results_df['Commission (Close)'].sum()
            total_funding_sum = results_df['Funding Paid/Received'].sum()
        else:
            total_pnl = 0
            total_commission_open_sum = 0
            total_commission_close_sum = 0
            total_funding_sum = 0
        
        logger.info(f"\n💰 TOTALS:")
        logger.info(f"  Total Open Commissions: {total_commission_open_sum:.6f}")
        logger.info(f"  Total Close Commissions: {total_commission_close_sum:.6f}")
        logger.info(f"  Total Funding: {total_funding_sum:.6f}")
        logger.info(f"  Total Realized PnL: {total_pnl:.6f}")
        
        return results_df, excel_filename if 'openpyxl' in globals() else csv_filename

def main():
    """Example usage with configurable date range"""
    HYPERLIQUID_ADDRESS = "0x6AA154D8fac6C8D7B9F9f5Cb8637FF6FBdF5AB81"
    BYBIT_API_KEY = "RmjkleMwl7PPiRlMhk"
    BYBIT_API_SECRET = "rfk9mOzHJu5HUv3MqI09muIHkZ4UbcvGufFp"
    
    analyzer = FundingArbitrageAnalyzer(HYPERLIQUID_ADDRESS, BYBIT_API_KEY, BYBIT_API_SECRET)
    
    # Example: Analyze performance for specified date range
    start_date = "2025-08-21"
    start_time = "15:47"
    end_date = "2025-08-25"
    end_time = "07:05"
    
    # Target coins
    target_coins = ['ENA', 'SOL']
    
    print(f"🚀 Starting funding arbitrage analysis (Bybit)")
    print(f"📅 Period: {start_date} {start_time} to {end_date} {end_time}")
    print(f"🎯 Tokens: {', '.join(target_coins)}")
    print("="*80)
    
    results, output_file = analyzer.analyze_performance(start_date, start_time, end_date, end_time, target_coins)
    
    print(f"\n🎉 Analysis complete! Output file: {output_file}")

if __name__ == "__main__":
    main()
##11:49 Aug 20 2025 ONDO
#15:47 Aug 21 2025 ENA SOL