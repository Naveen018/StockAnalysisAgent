from typing import Optional, List, Dict, Any
from pydantic import BaseModel, field_serializer
from datetime import datetime

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

class TickerAnalysis(BaseModel):
    ticker: str
    analysis: Optional[Dict[str, Any]] = None
    timeframe: str
    error: Optional[str] = None

class TickerIdentification(BaseModel):
    company_name: str
    ticker: str
    confidence: float
    timeframe: str = "last week"
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
    timeframe: Optional[str] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None

class NewsArticle(BaseModel):
    headline: str
    source: str
    published_at: str
    summary: Optional[str] = None
    url: Optional[str] = None

    @field_serializer('published_at')
    def serialize_published_at(self, published_at: str, _info):
        if isinstance(published_at, datetime):
            return published_at.isoformat()
        return published_at

class TickerNews(BaseModel):
    ticker: str
    news: List[NewsArticle]
    timeframe: str = "last week"
    error: Optional[str] = None

class SentimentAnalysis(BaseModel):
    positive: int
    negative: int
    neutral: int

class KeyEvent(BaseModel):
    date: str
    headline: str
    impact: str

    @field_serializer('date')
    def serialize_date(self, date: str, _info):
        if isinstance(date, datetime):
            return date.isoformat()
        return date