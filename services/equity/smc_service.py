import pandas as pd

# -----------------------------
# 1. Swing Detection
# -----------------------------
def detect_swings(df, left=3, right=3):
    swings = []
    for i in range(left, len(df)-right):
        local_high = df['high'][i-left:i+right+1].max()
        local_low = df['low'][i-left:i+right+1].min()
        if df['high'][i] == local_high:
            swings.append(('HH', df['high'][i], df.index[i]))
        elif df['low'][i] == local_low:
            swings.append(('LL', df['low'][i], df.index[i]))
    return swings

# -----------------------------
# 2. BOS / CHoCH Detection
# -----------------------------
def detect_bos_choch(swings):
    signals = []
    for i in range(1, len(swings)):
        prev_type, prev_price, prev_time = swings[i-1]
        curr_type, curr_price, curr_time = swings[i]

        if prev_type == 'HH' and curr_price < prev_price:
            signals.append(('CHoCH', curr_price, curr_time))
        elif prev_type == 'LL' and curr_price > prev_price:
            signals.append(('CHoCH', curr_price, curr_time))
        else:
            signals.append(('BOS', curr_price, curr_time))
    return signals

# -----------------------------
# 3. Order Blocks Detection
# -----------------------------
def detect_order_blocks(df, swings):
    order_blocks = []
    for i in range(1, len(swings)):
        prev_idx = df.index.get_loc(swings[i-1][2])
        curr_idx = df.index.get_loc(swings[i][2])
        high_block = df['high'][prev_idx:curr_idx].max()
        low_block = df['low'][prev_idx:curr_idx].min()
        if swings[i][0] == 'HH':
            order_blocks.append(('Bearish OB', low_block, high_block, swings[i-1][2], swings[i][2]))
        else:
            order_blocks.append(('Bullish OB', low_block, high_block, swings[i-1][2], swings[i][2]))
    return order_blocks

# -----------------------------
# 4. Fair Value Gaps (FVG)
# -----------------------------
def detect_fvg(df):
    fvg_list = []
    for i in range(1, len(df)-1):
        # Bullish gap
        if df['low'][i] > df['close'][i-1]:
            fvg_list.append(('Bullish FVG', df['close'][i-1], df['low'][i], df.index[i]))
        # Bearish gap
        elif df['high'][i] < df['close'][i-1]:
            fvg_list.append(('Bearish FVG', df['high'][i], df['close'][i-1], df.index[i]))
    return fvg_list

# -----------------------------
# 5. Full SMC Calculation
# -----------------------------
def calculate_smc(df):
    swings = detect_swings(df)
    signals = detect_bos_choch(swings)
    order_blocks = detect_order_blocks(df, swings)
    fvg_list = detect_fvg(df)
    return {
        'swings': swings,
        'signals': signals,
        'order_blocks': order_blocks,
        'fvg_list': fvg_list
    }