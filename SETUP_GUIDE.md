# Bybit Connector Setup Guide

## Prerequisites

1. Hummingbot installed and working
2. Bybit account with API credentials
3. Python 3.8 or higher

## Quick Start

### 1. Backup Existing Connectors

Before installing updates, backup your existing Bybit connectors:

```bash
# Backup exchange connector
cp -r /path/to/hummingbot/hummingbot/connector/exchange/bybit \
      /path/to/hummingbot/hummingbot/connector/exchange/bybit_backup

# Backup derivative connector  
cp -r /path/to/hummingbot/hummingbot/connector/derivative/bybit_perpetual \
      /path/to/hummingbot/hummingbot/connector/derivative/bybit_perpetual_backup
```

### 2. Install Updated Connectors

Copy the updated files to your Hummingbot installation:

```bash
# Copy exchange connector
cp -r exchange/* /path/to/hummingbot/hummingbot/connector/exchange/bybit/

# Copy derivative connector
cp -r derivative/* /path/to/hummingbot/hummingbot/connector/derivative/bybit_perpetual/

# Copy test files (optional)
cp -r test/* /path/to/hummingbot/test/hummingbot/connector/
```

### 3. Configure API Credentials

Add your Bybit API credentials to Hummingbot:

```bash
# Start Hummingbot
./start

# In Hummingbot console:
>>> connect bybit
Enter your Bybit API key >>>
Enter your Bybit secret key >>>
```

### 4. Test the Connection

Verify the connector is working:

```bash
# In Hummingbot console:
>>> balance
>>> status
```

## Using the Funding Arbitrage Analyzer

The funding arbitrage analyzer can be used standalone:

### 1. Install Dependencies

```bash
cd utils
pip install ccxt pandas numpy openpyxl requests
```

### 2. Configure the Analyzer

Edit `test_funding_arbitrage.py` with your credentials:

```python
HYPERLIQUID_ADDRESS = "your_hyperliquid_address"
BYBIT_API_KEY = "your_bybit_api_key"
BYBIT_API_SECRET = "your_bybit_api_secret"
```

### 3. Run Analysis

```bash
python test_funding_arbitrage.py
```

This will generate an Excel file with funding rate arbitrage opportunities.

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure API keys have correct permissions
   - Check if IP whitelist is configured
   - Verify API key/secret are correct

2. **Rate Limit Errors**
   - The updated connector handles this automatically
   - If persists, reduce request frequency in config

3. **WebSocket Disconnections**
   - Auto-reconnect is implemented
   - Check network connectivity
   - Verify firewall settings

4. **Order Errors**
   - Check account balance
   - Verify trading pair is correct
   - Ensure market is open

### Debug Mode

Enable debug logging for detailed information:

```python
# In your strategy or script
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Tips

1. **Use Testnet First**: Test strategies on Bybit testnet before live trading
2. **Monitor Rate Limits**: Watch the rate limit warnings in logs
3. **Optimize Pairs**: Don't subscribe to more pairs than needed
4. **Regular Updates**: Keep the connector updated for latest fixes

## Support Resources

- Hummingbot Discord: https://discord.hummingbot.io
- Bybit API Docs: https://bybit-exchange.github.io/docs/
- GitHub Issues: Report bugs in this repository

## Contributing

Found a bug or have an improvement? Contributions welcome!

1. Fork the repository
2. Create your feature branch
3. Test your changes thoroughly
4. Submit a pull request

Happy Trading! 🚀