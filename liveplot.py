import os 
import sys 
import threading 
from collections import deque 
from zoneinfo import ZoneInfo 

import matplotlib.dates as mdates 
import matplotlib.pyplot as plt 
from matplotlib.animation import FuncAnimation 

from alpaca.data.enums import DataFeed 
from alpaca.data.live import StockDataStream 

KEY = os.environ.get("ALPACA_API_KEY")
SECRET = os.environ.get("ALPACA_SECRET_KEY")

SYMBOL = (sys.argv[1] if len(sys.argv) > 1 else "AAPL").upper()

MAX_POINTS = 500 
REFRESH_MS = 1000
NY = ZoneInfo("America/New_York")

if not KEY or not SECRET:
    sys.exit("Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables first.")

times = deque(maxlen= MAX_POINTS)
prices = deque(maxlen= MAX_POINTS)
lock = threading.Lock()

async def on_trade(trade): 
    with lock: 
        times.append(mdates.date2num(trade.timestamp))
        prices.append(trade.price)

def run_stream(): 
    try: 
        stream = StockDataStream(KEY, SECRET, feed = DataFeed.IEX)
        stream.subscribe_trades(on_trade, SYMBOL)

        stream.run()

    except Exception as e: 
        print(f"Error: {e}")

threading.Thread(target = run_stream, daemon = True).start()

fig, ax = plt.subplots(figsize = (10,5))
(line,) = ax.plot([], [], lw=1.5)
ax.xaxis_date(tz=NY)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S", tz=NY))
ax.set_xlabel("Time (New York)")
ax.set_ylabel("Price ($)")
ax.set_title(f"{SYMBOL} (live trades, IEX)")
ax.grid(alpha=0.3)
fig.autofmt_xdate()
 
status = ax.text(
    0.5, 0.5, "Waiting for trades...",
    transform=ax.transAxes, ha="center", va="center", fontsize=14, color="gray",
)
 
 
def update_plot(_frame):
    with lock:
        x, y = list(times), list(prices)
 
    if not x:
        return line, status
 
    status.set_visible(False)
    line.set_data(x, y)
    ax.relim()
    ax.autoscale_view()
    ax.set_title(f"{SYMBOL}  |  last: ${y[-1]:.2f}  |  {len(y)} trades shown")
    return line, status
 
 
ani = FuncAnimation(fig, update_plot, interval=REFRESH_MS, cache_frame_data=False)
 
plt.show() 