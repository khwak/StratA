import os 
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document

class RAGEngine:
    def __init__(self):
        self.connection = os.environ.get("DATABASE_URL", "postgresql+psycopg://user:password@db:5432/strata_db")      
        self.collection_name = "hotel_reviews"

        print("[RAG] Connecting to PostgreSQL (pgvector) ...")

        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        self.vector_store = PGVector(
            embeddings=self.embeddings,
            collection_name=self.collection_name,
            connection=self.connection,
            use_jsonb=True,
        )

    def index_reviews(self, reviews: list):
        if not reviews:
            return
        print(f"\n[RAG] Indexing {len(reviews)} reviews to DB ...")
        docs = []
        for r in reviews:
            content = r.get("text", "")
            meta = {
                "date": r.get("date", ""),
                "rating": r.get("rating", 0),
                "is_internal": r.get("is_internal", True)
            }
            docs.append(Document(page_content=content, metadata=meta))
        
        self.vector_store.add_documents(docs)
        print("\n[RAG] Indexing Complete.")

    def retrieve_evidence(self, query: str, k: int = 3) -> list:
        fetch_k = max(k * 2, 6) 
        docs = self.vector_store.similarity_search(query, k=fetch_k)

        unique_evidence = []
        seen_texts = set()

        for d in docs:
            text = d.page_content.strip()
            
            if text not in seen_texts:
                seen_texts.add(text)
                unique_evidence.append(text)
            
            if len(unique_evidence) == k:
                break

        return unique_evidence
    
    def analyze_outliers(self, metrics_result: dict) -> list:
        queries = []

        kpi_scores = metrics_result.get("kpi_metrics", {}).get("scores", {})
        growth = metrics_result.get("growth_metrics", {})
        risks = metrics_result.get("risks", {}).get("current", [])
        
        for cat, score in kpi_scores.items():
            if isinstance(score, (int, float)) and score < 3.0:
                queries.append(f"{cat} 서비스 불만 및 문제점")
        
        for period_type in ['mom', 'yoy']:
            period_growth = growth.get(period_type, {}) 
            for cat, change in period_growth.items():
                if isinstance(change, (int, float)) and change < -0.5:
                    reason = "전월 대비" if period_type == 'mom' else "작년 대비"
                    queries.append(f"{cat} 지표가 {reason} 급락한 구체적 이유")

        for r in risks:
            topic_name = r.get('topic', '관련 이슈') 
            queries.append(f"호텔 {topic_name} 관련 구체적 사례")
        
        return list(set(queries))
    
try:
    rag_engine = RAGEngine()
except Exception as e:
    print(f"\n[RAG Error] DB 연결 실패.({e})")
    rag_engine = None