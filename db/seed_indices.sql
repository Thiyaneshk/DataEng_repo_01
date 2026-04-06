/**
 * PHASE 5: Seed Data - Master Indices and Key Constituents
 * 
 * Inserts master indices and sample constituents for:
 * - US: SPY (S&P 500), QQQ (Nasdaq 100), IWM (Russell 2000)
 * - India: NIFTY50, NIFTY_IT
 * - Canada: TSX60
 * 
 * Note: Weights are approximate as of April 2026
 */

-- ============================================================================
-- INSERT MASTER INDICES
-- ============================================================================

INSERT INTO indices (index_symbol, index_name, market, description, source, constituent_count)
VALUES
-- US Market
('SPY', 'S&P 500 ETF Trust', 'US', 'Tracks the 500 largest US companies', 'yfinance', 500),
('QQQ', 'Invesco QQQ Trust', 'US', 'Tracks the 100 largest non-financial stocks on Nasdaq', 'yfinance', 100),
('IWM', 'iShares Russell 2000 ETF', 'US', 'Tracks the 2000 small-cap US companies', 'yfinance', 2000),

-- India Market
('NIFTY50', 'NIFTY 50', 'IN', 'India''s top 50 large-cap stocks', 'nse', 50),
('NIFTY_IT', 'NIFTY IT Index', 'IN', 'India''s top IT companies', 'nse', 20),

-- Canada Market
('TSX60', 'S&P/TSX 60 Index', 'CA', 'Top 60 large-cap stocks on Toronto Stock Exchange', 'yahoo', 60)
ON CONFLICT (index_symbol) DO NOTHING;

-- ============================================================================
-- INSERT SPY (S&P 500) SAMPLE CONSTITUENTS
-- ============================================================================
INSERT INTO index_constituents (index_id, symbol, weight, sector, industry, company_name)
SELECT idx.index_id, data.symbol, data.weight, data.sector, data.industry, data.company_name
FROM (
    VALUES
    ('AAPL', 7.12, 'Technology', 'Consumer Electronics', 'Apple Inc.'),
    ('MSFT', 6.85, 'Technology', 'Software/Software as a Service', 'Microsoft Corporation'),
    ('GOOGL', 3.95, 'Communication Services', 'Internet and Related Services', 'Alphabet Inc.'),
    ('AMZN', 3.42, 'Consumer Discretionary', 'Internet and Direct Marketing Retail', 'Amazon.com Inc.'),
    ('NVDA', 3.12, 'Technology', 'Semiconductors', 'NVIDIA Corporation'),
    ('TSLA', 2.05, 'Consumer Discretionary', 'Automobile Manufacturers', 'Tesla Inc.'),
    ('META', 1.98, 'Communication Services', 'Internet Services', 'Meta Platforms Inc.'),
    ('BRK.B', 1.75, 'Financials', 'Investment Office/Holding Companies', 'Berkshire Hathaway Inc.'),
    ('JPM', 1.65, 'Financials', 'Banks', 'JPMorgan Chase & Co.'),
    ('JNJ', 1.50, 'Healthcare', 'Pharmaceuticals', 'Johnson & Johnson')
) AS data(symbol, weight, sector, industry, company_name)
CROSS JOIN indices idx WHERE idx.index_symbol = 'SPY'
ON CONFLICT (index_id, symbol) DO NOTHING;

-- ============================================================================
-- INSERT QQQ (NASDAQ 100) SAMPLE CONSTITUENTS
-- ============================================================================
INSERT INTO index_constituents (index_id, symbol, weight, sector, industry, company_name)
SELECT idx.index_id, data.symbol, data.weight, data.sector, data.industry, data.company_name
FROM (
    VALUES
    ('AAPL', 10.25, 'Technology', 'Consumer Electronics', 'Apple Inc.'),
    ('MSFT', 9.87, 'Technology', 'Software/Software as a Service', 'Microsoft Corporation'),
    ('NVDA', 4.50, 'Technology', 'Semiconductors', 'NVIDIA Corporation'),
    ('GOOGL', 5.65, 'Communication Services', 'Internet and Related Services', 'Alphabet Inc.'),
    ('AMZN', 4.92, 'Consumer Discretionary', 'Internet and Direct Marketing Retail', 'Amazon.com Inc.'),
    ('TSLA', 2.95, 'Consumer Discretionary', 'Automobile Manufacturers', 'Tesla Inc.'),
    ('META', 2.85, 'Communication Services', 'Internet Services', 'Meta Platforms Inc.'),
    ('ASML', 1.80, 'Technology', 'Semiconductor Equipment', 'ASML Holding N.V.'),
    ('AVGO', 1.45, 'Technology', 'Semiconductors', 'Broadcom Inc.'),
    ('INTC', 0.95, 'Technology', 'Semiconductors', 'Intel Corporation')
) AS data(symbol, weight, sector, industry, company_name)
CROSS JOIN indices idx WHERE idx.index_symbol = 'QQQ'
ON CONFLICT (index_id, symbol) DO NOTHING;

-- ============================================================================
-- INSERT IWM (RUSSELL 2000) SAMPLE CONSTITUENTS
-- ============================================================================
INSERT INTO index_constituents (index_id, symbol, weight, sector, industry, company_name)
SELECT idx.index_id, data.symbol, data.weight, data.sector, data.industry, data.company_name
FROM (
    VALUES
    ('RGEN', 0.15, 'Healthcare', 'Biotechnology', 'Repligen Corporation'),
    ('TXRH', 0.14, 'Consumer Discretionary', 'Restaurants', 'Texas Roadhouse Inc.'),
    ('KNSL', 0.12, 'Technology', 'Software', 'Kensington Capital'),
    ('SLAB', 0.11, 'Technology', 'Semiconductors', 'Silicon Laboratories Inc.'),
    ('SBUX', 0.13, 'Consumer Discretionary', 'Restaurants', 'Starbucks Corporation'),
    ('PFSI', 0.10, 'Financials', 'Banks', 'PennyMac Financial Services'),
    ('MANT', 0.11, 'Industrials', 'Aerospace and Defense', 'Mantech International'),
    ('AGYS', 0.09, 'Technology', 'IT Services', 'Agilysys Inc.'),
    ('CHPT', 0.08, 'Industrials', 'Electrical Equipment', 'ChargePoint Holdings'),
    ('CPRT', 0.12, 'Consumer Discretionary', 'Retail', 'Carpetright Limited')
) AS data(symbol, weight, sector, industry, company_name)
CROSS JOIN indices idx WHERE idx.index_symbol = 'IWM'
ON CONFLICT (index_id, symbol) DO NOTHING;

-- ============================================================================
-- INSERT NIFTY50 (INDIA) SAMPLE CONSTITUENTS
-- ============================================================================
INSERT INTO index_constituents (index_id, symbol, weight, sector, industry, company_name)
SELECT idx.index_id, data.symbol, data.weight, data.sector, data.industry, data.company_name
FROM (
    VALUES
    ('RELIANCE.NS', 11.95, 'Energy', 'Oil & Gas', 'Reliance Industries Limited'),
    ('TCS.NS', 9.25, 'Technology', 'IT Services', 'Tata Consultancy Services Limited'),
    ('HDFCBANK.NS', 8.50, 'Financials', 'Banks', 'HDFC Bank Limited'),
    ('ICICIBANK.NS', 6.10, 'Financials', 'Banks', 'ICICI Bank Limited'),
    ('KOTAKBANK.NS', 5.25, 'Financials', 'Banks', 'Kotak Mahindra Bank Limited'),
    ('HINDUNILVR.NS', 3.40, 'Consumer Discretionary', 'Fast-Moving Consumer Goods', 'Hindustan Unilever Limited'),
    ('WIPRO.NS', 2.55, 'Technology', 'IT Services', 'Wipro Limited'),
    ('SBIN.NS', 2.90, 'Financials', 'Banks', 'State Bank of India'),
    ('LT.NS', 2.45, 'Industrials', 'Engineering & Construction', 'Larsen & Toubro Limited'),
    ('INFY.NS', 2.80, 'Technology', 'IT Services', 'Infosys Limited')
) AS data(symbol, weight, sector, industry, company_name)
CROSS JOIN indices idx WHERE idx.index_symbol = 'NIFTY50'
ON CONFLICT (index_id, symbol) DO NOTHING;

-- ============================================================================
-- INSERT NIFTY_IT (INDIA IT INDEX) SAMPLE CONSTITUENTS
-- ============================================================================
INSERT INTO index_constituents (index_id, symbol, weight, sector, industry, company_name)
SELECT idx.index_id, data.symbol, data.weight, data.sector, data.industry, data.company_name
FROM (
    VALUES
    ('TCS.NS', 22.15, 'Technology', 'IT Services', 'Tata Consultancy Services Limited'),
    ('INFY.NS', 15.85, 'Technology', 'IT Services', 'Infosys Limited'),
    ('WIPRO.NS', 12.50, 'Technology', 'IT Services', 'Wipro Limited'),
    ('HCL-INSYS.NS', 10.45, 'Technology', 'IT Services', 'HCL Technologies Limited'),
    ('TECH.NS', 8.20, 'Technology', 'IT Services', 'Persistent Systems Limited'),
    ('LTTS.NS', 6.15, 'Technology', 'IT Services', 'L&T Technology Services'),
    ('MPHASIS.NS', 5.80, 'Technology', 'IT Services', 'MphasiS Limited'),
    ('BLKTI.NS', 4.45, 'Technology', 'IT Consulting', 'BL India Ltd'),
    ('ZCAL.NS', 3.25, 'Technology', 'IT Services', 'Zensar Technologies Limited'),
    ('CGSPL.NS', 2.90, 'Technology', 'IT Services', 'Cognizant Enterprises Limited')
) AS data(symbol, weight, sector, industry, company_name)
CROSS JOIN indices idx WHERE idx.index_symbol = 'NIFTY_IT'
ON CONFLICT (index_id, symbol) DO NOTHING;

-- ============================================================================
-- INSERT TSX60 (CANADA) SAMPLE CONSTITUENTS
-- ============================================================================
INSERT INTO index_constituents (index_id, symbol, weight, sector, industry, company_name)
SELECT idx.index_id, data.symbol, data.weight, data.sector, data.industry, data.company_name
FROM (
    VALUES
    ('TD.TO', 10.15, 'Financials', 'Banks', 'Toronto Dominion Bank'),
    ('RY.TO', 9.85, 'Financials', 'Banks', 'Royal Bank of Canada'),
    ('BNS.TO', 8.25, 'Financials', 'Banks', 'Bank of Nova Scotia'),
    ('CM.TO', 7.45, 'Financials', 'Banks', 'Canadian Imperial Bank of Commerce'),
    ('BCE.TO', 4.50, 'Communication Services', 'Telecommunications', 'BCE Inc.'),
    ('ENB.TO', 3.95, 'Energy', 'Oil & Gas Transportation', 'Enbridge Inc.'),
    ('TRP.TO', 3.65, 'Energy', 'Oil & Gas Transportation', 'TC Energy Corporation'),
    ('ACQ.TO', 2.85, 'Industrials', 'Airlines', 'Air Canada'),
    ('CP.TO', 2.45, 'Industrials', 'Railroads', 'Canadian Pacific Railway Limited'),
    ('CNQ.TO', 2.10, 'Energy', 'Oil & Gas Exploration & Production', 'Canadian Natural Resources')
) AS data(symbol, weight, sector, industry, company_name)
CROSS JOIN indices idx WHERE idx.index_symbol = 'TSX60'
ON CONFLICT (index_id, symbol) DO NOTHING;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Uncomment to verify data was loaded:
/*
SELECT * FROM indices;
SELECT i.index_symbol, COUNT(ic.constituent_id) as constituent_count
FROM indices i
LEFT JOIN index_constituents ic ON i.index_id = ic.index_id
GROUP BY i.index_symbol
ORDER BY i.index_symbol;
*/
