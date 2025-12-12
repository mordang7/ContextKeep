from datetime import datetime
try:
    from zoneinfo import ZoneInfo
    jst = ZoneInfo("Asia/Tokyo")
    print(f"JST Time: {datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S %Z')}")
except ImportError:
    print("ZoneInfo not found")
except Exception as e:
    print(f"Error: {e}")
