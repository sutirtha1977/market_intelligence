git add .
git commit -m "changes done on 30 Aug 2026"
git push

ps aux | grep -E "zsh|bash|fish" | grep -v grep | awk '{print $2}' | xargs kill -9
brew services start postgresql@14

source venv/bin/activate

python -m pip freeze > requirements.txt

1. Work on derivative data
2. IV how to use
3. how to combine derivatives data to get meaningful insights 

-------------------
SELECT
  symbol_id,
  MAX(date) AS max_date
FROM yahoo_india_index_price
GROUP BY symbol_id
ORDER BY symbol_id;
-------------------
SELECT
    s.symbol,
    i.date,
    ROUND(p.adj_close::numeric, 2) AS adj_close,
    ROUND(i.rsi_10_ema_21::numeric, 2) AS rsi_10_ema_21
FROM yahoo_india_equity_indicators i
INNER JOIN yahoo_india_equity_symbols s
    ON s.symbol_id = i.symbol_id
INNER JOIN yahoo_india_equity_price p
    ON p.symbol_id = i.symbol_id
   AND p.timeframe = i.timeframe
   AND p.date = i.date
WHERE
    s.is_active = TRUE
    AND i.timeframe = '1d'
    AND i.date = (
        SELECT MAX(date)
        FROM yahoo_india_equity_indicators
        WHERE timeframe = '1d'
    )
    AND i.rsi_10_ema_21 < 10
	AND i.rsi_10_ema_21 >8
    AND p.adj_close > 100
ORDER BY
    i.rsi_10_ema_21 ASC,
    s.symbol;
-----------------------


