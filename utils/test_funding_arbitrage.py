import sys
sys.path.append('/home/ubuntu/sheets')
from simpleExtract_v3 import FundingArbitrageAnalyzer
from datetime import datetime, timedelta

# Test with recent dates
HYPERLIQUID_ADDRESS = "0x6AA154D8fac6C8D7B9F9f5Cb8637FF6FBdF5AB81"
BYBIT_API_KEY = "RmjkleMwl7PPiRlMhk"
BYBIT_API_SECRET = "rfk9mOzHJu5HUv3MqI09muIHkZ4UbcvGufFp"

analyzer = FundingArbitrageAnalyzer(HYPERLIQUID_ADDRESS, BYBIT_API_KEY, BYBIT_API_SECRET)

# Test with just 1 day of recent data
end_date = datetime.now()
start_date = end_date - timedelta(days=1)

start_str = start_date.strftime("%Y-%m-%d")
start_time = start_date.strftime("%H:%M")
end_str = end_date.strftime("%Y-%m-%d") 
end_time = end_date.strftime("%H:%M")

# Test with just one coin to make it faster
target_coins = ['BTC']

print(f"🚀 Testing Bybit integration")
print(f"📅 Period: {start_str} {start_time} to {end_str} {end_time}")
print(f"🎯 Testing with: {', '.join(target_coins)}")
print("="*80)

try:
    results, output_file = analyzer.analyze_performance(start_str, start_time, end_str, end_time, target_coins)
    print(f"\n✅ Test completed successfully!")
    print(f"📄 Output file: {output_file}")
except Exception as e:
    print(f"\n❌ Test failed with error: {e}")
    import traceback
    traceback.print_exc()