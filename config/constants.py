# config/constants.py

# ---------------- FREQUENCIES ----------------
FREQUENCIES = ["1d", "1wk", "1mo"]

# ---------------- NSE URLs ----------------
NIFTY_INDEX_URLS = {
    "Nifty 50": "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv",
    "Nifty Next 50": "https://www.niftyindices.com/IndexConstituent/ind_niftynext50list.csv",
    "Nifty 100": "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv",
    "Nifty 200": "https://www.niftyindices.com/IndexConstituent/ind_nifty200list.csv",
    "Nifty Total Market": "https://www.niftyindices.com/IndexConstituent/ind_niftytotalmarket_list.csv",
    "Nifty 500": "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv",
    "Nifty Midcap 50": "https://www.niftyindices.com/IndexConstituent/ind_niftymidcap50list.csv",
    "Nifty Midcap Select": "https://www.niftyindices.com/IndexConstituent/ind_niftymidcapselect_list.csv",
    "Nifty Midcap 100": "https://www.niftyindices.com/IndexConstituent/ind_niftymidcap100list.csv",
    "Nifty Smallcap 500": "https://www.niftyindices.com/IndexConstituent/ind_NiftySmallcap500_list.csv",
    "Nifty Smallcap 250": "https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap250list.csv",
    "Nifty Smallcap 50": "https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap50list.csv",
    "Nifty Smallcap 100": "https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap100list.csv",
    "Nifty Microcap 250": "https://www.niftyindices.com/IndexConstituent/ind_niftymicrocap250_list.csv",
    "Nifty LargeMidcap 250": "https://www.niftyindices.com/IndexConstituent/ind_niftylargemidcap250list.csv",
    "Nifty MidSmallcap 400": "https://www.niftyindices.com/IndexConstituent/ind_niftymidsmallcap400list.csv",
    "Nifty India FPI 150": "https://www.niftyindices.com/IndexConstituent/ind_niftyIndiaFPI150_list.csv",
    "Nifty Auto": "https://www.niftyindices.com/IndexConstituent/ind_niftyautolist.csv",
    "Nifty Bank": "https://www.niftyindices.com/IndexConstituent/ind_niftybanklist.csv",
    "Nifty Cement": "https://www.niftyindices.com/IndexConstituent/ind_NiftyCement_list.csv",
    "Nifty Chemicals": "https://www.niftyindices.com/IndexConstituent/ind_niftyChemicals_list.csv",
    "Nifty Financial Services": "https://www.niftyindices.com/IndexConstituent/ind_niftyfinancelist.csv",
    "Nifty FMCG": "https://www.niftyindices.com/IndexConstituent/ind_niftyfmcglist.csv",
    "Nifty IT": "https://www.niftyindices.com/IndexConstituent/ind_niftyitlist.csv",
    "Nifty Media": "https://www.niftyindices.com/IndexConstituent/ind_niftymedialist.csv",
    "Nifty Metal": "https://www.niftyindices.com/IndexConstituent/ind_niftymetallist.csv",
    "Nifty Pharma": "https://www.niftyindices.com/IndexConstituent/ind_niftypharmalist.csv",
    "Nifty Private Bank": "https://www.niftyindices.com/IndexConstituent/ind_nifty_privatebanklist.csv",
    "Nifty PSU Bank": "https://www.niftyindices.com/IndexConstituent/ind_niftypsubanklist.csv",
    "Nifty Realty": "https://www.niftyindices.com/IndexConstituent/ind_niftyrealtylist.csv",
    "Nifty Consumer Durables": "https://www.niftyindices.com/IndexConstituent/ind_niftyconsumerdurableslist.csv",
    "Nifty Oil and Gas": "https://www.niftyindices.com/IndexConstituent/ind_niftyoilgaslist.csv",
    "Nifty500 Healthcare": "https://www.niftyindices.com/IndexConstituent/ind_nifty500Healthcare_list.csv",
    "Nifty Capital Markets": "https://www.niftyindices.com/IndexConstituent/ind_niftyCapitalMarkets_list.csv",
    "Nifty Commodities": "https://www.niftyindices.com/IndexConstituent/ind_niftycommoditieslist.csv",
    "Nifty Conglomerate 50": "https://www.niftyindices.com/IndexConstituent/ind_niftyConglomerate50_list.csv",
    "Nifty Core Housing": "https://www.niftyindices.com/IndexConstituent/ind_niftyCoreHousing_list.csv",
    "Nifty CPSE": "https://www.niftyindices.com/IndexConstituent/ind_niftycpselist.csv",
    "Nifty Energy": "https://www.niftyindices.com/IndexConstituent/ind_niftyenergylist.csv",
    "Nifty EV & New Age Automotive": "https://www.niftyindices.com/IndexConstituent/ind_niftyEv_NewAgeAutomotive_list.csv",
    "Nifty Housing": "https://www.niftyindices.com/IndexConstituent/ind_niftyhousing_list.csv",
    "Nifty India Consumption": "https://www.niftyindices.com/IndexConstituent/ind_niftyconsumptionlist.csv",
    "Nifty India Defence": "https://www.niftyindices.com/IndexConstituent/ind_niftyindiadefence_list.csv",
    "Nifty India Digital": "https://www.niftyindices.com/IndexConstituent/ind_niftyindiadigital_list.csv",
    "Nifty India Infrastructure & Logistics": "https://www.niftyindices.com/IndexConstituent/ind_niftyIndiaInfrastructure_Logistics_list.csv",
    "Nifty India Internet": "https://www.niftyindices.com/IndexConstituent/ind_niftyIndiaInternet_list.csv",
    "Nifty India Manufacturing": "https://www.niftyindices.com/IndexConstituent/ind_niftyindiamanufacturing_list.csv",
    "Nifty India New Age Consumption": "https://www.niftyindices.com/IndexConstituent/ind_niftyIndiaNewAgeConsumption_list.csv",
    "Nifty India Railways PSU": "https://www.niftyindices.com/IndexConstituent/ind_niftyIndiaRailwaysPSU_list.csv",
    "Nifty India Tourism": "https://www.niftyindices.com/IndexConstituent/ind_niftyindiatourism_list.csv",
    "Nifty Infrastructure": "https://www.niftyindices.com/IndexConstituent/ind_niftyinfralist.csv",
    "Nifty IPO": "https://www.niftyindices.com/IndexConstituent/ind_niftyIPO_list.csv",
    "Nifty MNC": "https://www.niftyindices.com/IndexConstituent/ind_niftymnclist.csv",
    "Nifty Mobility": "https://www.niftyindices.com/IndexConstituent/ind_niftymobility_list.csv",
    "Nifty PSE": "https://www.niftyindices.com/IndexConstituent/ind_niftypselist.csv",
    "Nifty Rural": "https://www.niftyindices.com/IndexConstituent/ind_niftyRural_list.csv",
    "Nifty Non-Cyclical Consumer": "https://www.niftyindices.com/IndexConstituent/ind_niftynon-cyclicalconsumer_list.csv",
    "Nifty Services Sector": "https://www.niftyindices.com/IndexConstituent/ind_niftyservicelist.csv",
    "Nifty Transportation & Logistics": "https://www.niftyindices.com/IndexConstituent/ind_niftytransportationandlogistics_list.csv",
    "Nifty Waves": "https://www.niftyindices.com/IndexConstituent/ind_niftyWaves_list.csv"
}
# ---------------- NSE URLs ----------------
NSE_IDX_API_URL = (
    "https://www.niftyindices.com/"
    "BackPage/getHistoricaldatatabletoString"
)

NSE_DAILY_URL = (
    "https://www.niftyindices.com/"
    "Daily_Snapshot/ind_close_all_{date}.csv"
)

NSE_IDX_HEADERS = {
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

NSE_IDX_CONS_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.niftyindices.com/",
    "Accept": "*/*",
}
