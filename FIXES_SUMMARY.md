# Bybit Connector Fixes Summary

## Issue Summary
The Bybit funding rate arbitrage strategy was stopping too quickly (within 10 minutes) due to funding rate stop loss triggers. Investigation revealed several issues with the Bybit connector compared to Binance/Hyperliquid.

## Fixes Implemented

### 1. Reduced Funding Fee Poll Interval
**File**: `bybit_perpetual_derivative.py`
- Changed `funding_fee_poll_interval` from 120 seconds (2 minutes) to 600 seconds (10 minutes)
- This matches Binance's polling interval and reduces API calls

### 2. Wallet Balance Caching
**File**: `bybit_perpetual_derivative.py`
- Added wallet balance caching with 30-second TTL
- Added available balance caching per coin with 30-second TTL
- Prevents hitting API rate limits (120 calls/60s on wallet balance endpoint)

### 3. Funding Rate Validation
**Files**: `bybit_perpetual_derivative.py`, `bybit_perpetual_api_order_book_data_source.py`
- Added validation to check funding rates are within reasonable bounds (-0.1% to 0.1% per hour)
- In main connector: Returns None on invalid rates to trigger fallback
- In order book data source: Clamps unusual values to reasonable bounds
- Prevents spurious funding rate values from triggering stop losses

### 4. WebSocket Reconnection with Exponential Backoff
**Files**: `bybit_perpetual_api_order_book_data_source.py`, `bybit_perpetual_user_stream_data_source.py`
- Implemented exponential backoff for reconnection attempts
- Delay calculation: 5 * 2^attempts seconds, capped at 300 seconds (5 minutes)
- Resets attempt counter on successful connection
- Improves error logging with attempt count and delay information

## API Rate Limiting Issues Found
1. Wallet balance endpoint: 120 calls per 60 seconds limit (fixed with caching)
2. Funding fee polling too aggressive at 2-minute intervals (fixed by increasing to 10 minutes)
3. WebSocket disconnections with code 1006 (improved with exponential backoff)

## Testing Recommendations
1. Monitor funding rate values in logs to ensure validation is working
2. Check that wallet balance API calls are reduced
3. Verify WebSocket reconnections use exponential backoff on failures
4. Run the strategy for extended periods to confirm stop losses aren't triggered prematurely

## Notes
- ENA/SOL/ONDO pairs were not found in the logs despite user expectations
- The bot was only trading IP-USDT and KAITO-USDT pairs in the analyzed logs
- Funding rate stop losses were legitimate based on rate differentials, but validation should prevent spurious triggers