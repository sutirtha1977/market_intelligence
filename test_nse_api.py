
import requests
import json
import pandas as pd

START_DATE = "01-Jan-2000"
END_DATE = "31-Dec-2017"

NSE_IDX_API_URL = (
    "https://www.niftyindices.com/"
    "BackPage/getHistoricaldatatabletoString"
)

HEADERS = {
    "Content-Type": "application/json; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://www.niftyindices.com",
    "Referer": "https://www.niftyindices.com/reports/historical-data",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
}


def get_nifty_50_history():

    symbol = "NIFTY 50"

    cinfo = (
        f"{{'name':'{symbol}',"
        f"'startDate':'{START_DATE}',"
        f"'endDate':'{END_DATE}',"
        f"'indexName':'{symbol}'}}"
    )

    payload = {"cinfo": cinfo}

    with requests.Session() as session:

        session.headers.update(HEADERS)

        session.get(
            "https://www.niftyindices.com/",
            timeout=30
        )

        session.get(
            "https://www.niftyindices.com/reports/historical-data",
            timeout=30
        )

        response = session.post(
            NSE_IDX_API_URL,
            json=payload,
            timeout=60,
            allow_redirects=False
        )

        if response.status_code != 200:
            print(
                f"Unable to retrieve {symbol} data. "
                f"HTTP Status: {response.status_code}"
            )
            print("Redirect:", response.headers.get("Location"))
            return

        # Parse API response
        try:
            result = response.json()
        except ValueError:
            print("API returned invalid JSON.")
            print(response.text[:500])
            return

        # Handle list or dictionary response
        if isinstance(result, list):

            records = result

        elif isinstance(result, dict):

            raw = result.get("d")

            if not raw:
                print(f"No historical data returned for {symbol}.")
                return

            records = (
                json.loads(raw)
                if isinstance(raw, str)
                else raw
            )

        else:

            print(
                f"Unexpected API response: "
                f"{type(result).__name__}"
            )
            return

        if not records:
            print(f"No historical records found for {symbol}.")
            return

        df = pd.DataFrame(records)

        df.rename(
            columns={
                "HistoricalDate": "Date",
                "OPEN": "Open",
                "HIGH": "High",
                "LOW": "Low",
                "CLOSE": "Close",
            },
            inplace=True
        )

        if "Date" not in df.columns:
            print("Historical date column not found.")
            print("Available columns:", df.columns.tolist())
            return

        df["Date"] = pd.to_datetime(
            df["Date"],
            format="%d %b %Y",
            errors="coerce"
        )

        df = df.dropna(subset=["Date"])

        df = df[
            (df["Date"] >= pd.to_datetime(START_DATE)) &
            (df["Date"] <= pd.to_datetime(END_DATE))
        ]

        df = df.sort_values("Date")

        columns = ["Date", "Open", "High", "Low", "Close"]

        print("\nNIFTY 50 HISTORICAL DATA")
        print(f"Period: {START_DATE} to {END_DATE}")
        print("=" * 75)

        if df.empty:
            print("No records available for the requested period.")
        else:
            print(df[columns].to_string(index=False))

        print("=" * 75)
        print(f"Total records: {len(df)}")


if __name__ == "__main__":
    get_nifty_50_history()
