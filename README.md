# Bybit Connector Updates for Hummingbot

This repository contains updated and enhanced Bybit connector implementations for Hummingbot, including both spot and perpetual trading support.

## Overview

These updates improve the Bybit connector functionality in Hummingbot with:
- Enhanced error handling and retry mechanisms
- Improved rate limiting compliance
- Better funding rate data collection
- Fixed authentication issues
- Support for both spot and perpetual markets

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

Contributions are welcome! Please ensure:
1. All tests pass before submitting PR
2. Code follows Hummingbot coding standards
3. New features include appropriate tests
4. Documentation is updated accordingly

## License

This code is provided under the same license as Hummingbot. See the main Hummingbot repository for license details.

## Support

For issues and questions:
- Open an issue in this repository
- Join the Hummingbot Discord community
- Check the Hummingbot documentation

## Bounty Program

If you find these updates useful, consider supporting through the Hummingbot bounty program. These improvements help the entire community trade more effectively on Bybit.