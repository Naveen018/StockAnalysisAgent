from typing import Optional, List
from pydantic import BaseModel

class PriceChange(BaseModel):
    absolute_change: float
    percentage_change: float
    start_price: float
    end_price: float
    timeframe: str

class TickerPriceChange(BaseModel):
    ticker: str
    price_change: Optional[PriceChange] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    error: Optional[str] = None

class NewsItem(BaseModel):
    headline: str
    published_at: str

class Analysis(BaseModel):
    summary: str
    price_change: Optional[PriceChange] = None
    key_news: List[NewsItem] = []

class TickerAnalysis(BaseModel):
    ticker: str
    analysis: Optional[Analysis] = None
    error: Optional[str] = None

class TickerIdentification(BaseModel):
    company_name: str
    ticker: str
    confidence: float
    error: Optional[str] = None
    original_query: str 

class PriceData(BaseModel):
    current: float
    open: float
    high: float
    low: float

class TickerPrice(BaseModel):
    ticker: str
    price: Optional[PriceData] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None

class NewsArticle(BaseModel):
    headline: str
    source: str
    published_at: str
    summary: Optional[str] = None
    url: Optional[str] = None

class TickerNews(BaseModel):
    ticker: str
    news: List[NewsArticle]
    error: Optional[str] = None