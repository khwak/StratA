import os
import json
import pandas as pd
import requests
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import urllib.parse

load_dotenv()

class StandardReview(BaseModel):
    text: str = Field(description="리뷰 원문")
    rating: int = Field(default=0, description="별점/평점")
    date: str = Field(default="", description="작성일")
    is_internal: bool = Field(description="자사 데이터 여부")

class CollectorEngine:
    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.path.join(os.getcwd(), "data")
        self.news_api_key = os.getenv("NEWS_API_KEY")

    def fetch_reviews(self, source_type: str, file_name: str, period: str = None) -> List[Dict[str, Any]]:
        print(f"\n[API] Connecting to {source_type} Gateway...")
        path = os.path.join(self.base_path, file_name)

        if not os.path.exists(path):
            print(f"\n[ERROR] API Connection Failed: {file_name} not found.")
            return []

        if file_name.endswith('.csv'):
            df = pd.read_csv(path)
        else:
            with open(path, "r", encoding="utf-8") as f:
                df = pd.DataFrame(json.load(f))

        if period and 'date' in df.columns:
            if 'Q' in period: 
                year, q = period.split('-Q')
                df['dt'] = pd.to_datetime(df['date'], errors='coerce')
                quarter_map = {"1": [1,2,3], "2": [4,5,6], "3": [7,8,9], "4": [10,11,12]}
                df = df.dropna(subset=['dt'])
                df = df[(df['dt'].dt.year == int(year)) & (df['dt'].dt.month.isin(quarter_map[q]))]
            else: 
                df = df[df['date'].str.startswith(period, na=False)]

        is_internal = "internal" in source_type.lower()
        standardized = []

        for _, row in df.iterrows():
            review_obj = StandardReview(
                text=str(row.get("text") or row.get("content") or ""),
                rating=int(row.get("rating") or row.get("score") or 0),
                date=str(row.get("date") or ""),
                is_internal=is_internal
            )
            standardized.append(review_obj.model_dump())

        print(f"\n[SUCCESS] {len(standardized)} standardized reviews fetched.")
        return standardized

    # 내부 메타데이터 로드
    def fetch_internal_info(self, file_name: str) -> Dict[str, Any]:
        path = os.path.join(self.base_path, file_name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"\n[SUCCESS] Internal Metadata for '{data.get('hotel_name')}' loaded.")
            return data
        except Exception as e:
            print(f"\n[WARNING] Using default metadata due to error: {e}")
            return {"hotel_name": "Default Hotel", "amenities": []}
    
    # 외부 뉴스/트랜드 수집
    def fetch_external_trends(self) -> List[str]:
        print("\n[API] Fetching Real-time Industry Trends via NewsAPI...")

        if not self.news_api_key:
            print("\n[ERROR] News API Key is missing. Check your .env file.")
            return ["API 키 누락으로 트렌드를 가져올 수 없습니다."]


        positive_keywords = "증가 OR 상승 OR 회복 OR 확대 OR 성장 OR 매출 증가 OR 실적 개선 OR 흑자 전환 OR 도입 OR 혁신 OR 자동화 OR 디지털 전환 OR 확장 OR 리뉴얼 OR 제휴 OR 글로벌 진출"
        negative_keywords = "감소 OR 하락 OR 둔화 OR 침체 OR 비용 증가 OR 인건비 상승 OR 수익성 악화 OR 적자 OR 규제 강화 OR 세금 인상 OR 제한 OR 논란 OR 불만 OR 분쟁 OR 운영 차질"
        # query = f"호텔 AND ({positive_keywords} OR {negative_keywords})"
        query = "호텔 AND (트렌드 OR 동향 OR 기술 OR 서비스 OR 리스크)"

        params = {
            "q": query,
            "sortBy": "publishedAt",
            "language": "ko",
            "pageSize": 10, 
            "apiKey": self.news_api_key
        }

        try: 
            url = "https://newsapi.org/v2/everything"
            max_retries = 3 
        
            for attempt in range(max_retries):
                try: 
                    response = requests.get(url, params=params, timeout=5)
                    response.raise_for_status() 
                    
                    data = response.json()

                    if data.get("status") == "ok":
                        articles = data.get("articles", [])
                        trends = [article['title'] for article in articles]

                        if not trends:
                            print("[INFO] No specific news found. Returning default trends.")
                            return ["2026 글로벌 호텔 위생 표준 강화", "친환경 어메니티 규제 대응 현황"]
                        
                        print(f"[SUCCESS] {len(trends)} news headlines fetched.")
                        return trends
                    else:
                        print(f"[ERROR] NewsAPI Error: {data.get('message')}")
                        return ["뉴스 데이터를 불러올 수 없어 기본 트렌드를 반환합니다."]
                    
                except requests.exceptions.RequestException as e:
                    print(f"[WARNING] NewsAPI Request failed (Attempt {attempt+1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)  
                    else:
                        print("[ERROR] NewsAPI 최대 재시도 횟수를 초과했습니다.")
                        return ["트렌드 수집 중 네트워크 오류가 발생했습니다."]
            
        except Exception as e:
            print(f"[ERROR] NewsAPI Request failed: {e}")
            return ["트렌드 수집 중 네트워크 오류가 발생했습니다."]
        
collector_engine = CollectorEngine()