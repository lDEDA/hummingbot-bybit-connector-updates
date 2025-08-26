# Bybit Connector Updates for Hummingbot

Independent improvements and fixes for the Hummingbot Bybit connector, addressing various issues and adding enhanced functionality for both spot and perpetual trading.

## Overview

I've been working with the Hummingbot Bybit connector and encountered several issues that needed fixing. This repository contains my solutions and improvements:
- Fixed authentication problems with Bybit API v5
- Resolved rate limiting issues that were causing disconnections
- Improved WebSocket stability and reconnection logic
- Added better error handling and recovery
- Created tools for funding rate arbitrage analysis

## Features

### Exchange Connector (Spot Trading)
- Full spot trading support with improved order management
- Enhanced WebSocket handling for real-time data
- Better error recovery and connection stability
- Optimized rate limiting to prevent API errors

### Derivative Connector (Perpetual Trading)
- Complete perpetual/futures trading support
- Real-time funding rate tracking
- Position management improvements
- Enhanced margin and leverage handling

### Funding Arbitrage Tools
- `funding_arbitrage_analyzer.py`: Comprehensive tool for analyzing funding rate arbitrage opportunities
- Support for comparing Bybit perpetual funding rates with other exchanges
- Historical data analysis capabilities
- Real-time monitoring features

## Installation

1. Copy the connector files to your Hummingbot installation:
```bash
# For exchange connector
cp -r exchange/* /path/to/hummingbot/hummingbot/connector/exchange/bybit/

# For derivative connector  
cp -r derivative/* /path/to/hummingbot/hummingbot/connector/derivative/bybit_perpetual/

# For test files
cp -r test/* /path/to/hummingbot/test/hummingbot/connector/
```

2. The funding arbitrage analyzer can be used independently:
```bash
cd utils
python funding_arbitrage_analyzer.py
```

## Key Improvements

### Authentication Fixes
- Fixed signature generation for API v5
- Improved timestamp synchronization
- Better handling of API key permissions

### Rate Limiting
- Implemented proper rate limit tracking per endpoint
- Automatic request throttling
- Exponential backoff on rate limit errors

### WebSocket Enhancements
- More stable connection management
- Automatic reconnection with state recovery
- Better handling of subscription limits

### Error Handling
- Comprehensive error classification
- Proper retry logic for recoverable errors
- Clear error messages for debugging

## Usage Example

### Basic Setup
```python
from hummingbot.connector.exchange.bybit import bybit_exchange
from hummingbot.connector.derivative.bybit_perpetual import bybit_perpetual

# Initialize connectors
exchange = bybit_exchange.BybitExchange(
    api_key="your_api_key",
    secret_key="your_secret_key",
    trading_pairs=["BTC-USDT", "ETH-USDT"]
)

perpetual = bybit_perpetual.BybitPerpetualDerivative(
    api_key="your_api_key", 
    secret_key="your_secret_key",
    trading_pairs=["BTC-USDT", "ETH-USDT"]
)
```

### Funding Rate Arbitrage Analysis
```python
from utils.funding_arbitrage_analyzer import FundingArbitrageAnalyzer

analyzer = FundingArbitrageAnalyzer(
    hyperliquid_address="your_address",
    bybit_api_key="your_api_key",
    bybit_api_secret="your_secret"
)

# Analyze arbitrage opportunities
results = analyzer.analyze_performance(
    start_date="2024-01-01",
    start_time="00:00",
    end_date="2024-01-31", 
    end_time="23:59",
    target_coins=["BTC", "ETH", "SOL"]
)
```

## Testing

Run the test suite to verify functionality:
```bash
# Test exchange connector
python -m pytest test/exchange/

# Test derivative connector  
python -m pytest test/derivative/

# Test funding arbitrage analyzer
cd utils
python test_funding_arbitrage.py
```

## Contributing

Feel free to submit issues or pull requests if you find bugs or have improvements. When contributing:
1. Test your changes thoroughly
2. Include clear descriptions of what was changed and why
3. Update documentation if adding new features

## License

This code is provided as-is for the Hummingbot community. Feel free to use and modify as needed.

## Support

If you encounter issues or have questions about these updates:
- Open an issue in this repository
- Check the Hummingbot Discord for community support
- Refer to Bybit's API documentation for endpoint-specific questions

## Disclaimer

These are independent modifications not officially supported by Hummingbot or Bybit. Use at your own risk and always test thoroughly before using in production.