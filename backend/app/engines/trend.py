from langchain_openai import ChatOpenAI

class TrendEngine:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    def generate_trend_insights(self, my_trends: list, external_trends: list) -> list:
        print("\n[Trend Engine] 외부 뉴스 기반 AI 비즈니스 인사이트 도출 중...")
        emerging_trends_formatted = []
        
        for i, trend in enumerate(my_trends[:2]):
            topic_name = trend.get("topic", "New Trend")
            keywords = trend.get("keywords", [])[:3]
            count = trend.get("count", 0)
            
            trend_title = " & ".join(keywords[:2]) if len(keywords) >= 2 else topic_name
            news_context = external_trends[i] if i < len(external_trends) else "최신 호텔 서비스 동향"

            prompt = f"""
            당신은 글로벌 호텔 체인의 비즈니스 분석가입니다.
            우리 호텔의 최근 고객 리뷰에서 '{', '.join(keywords)}' 관련 키워드가 {count}건 포착되었습니다.
            한편, 최근 시장 뉴스의 헤드라인은 다음과 같습니다: "{news_context}"

            이 두 가지 사실(고객 리뷰 키워드와 시장 뉴스)을 논리적으로 연결하여 2~3문장의 깊이 있는 비즈니스 인사이트를 도출하세요.
            [중요 조건]
            만약 두 내용이 억지스럽거나 전혀 관련이 없다면, 억지로 연결하지 마세요! 그럴 경우 뉴스 내용은 무시하고, 우리 호텔에서 포착된 키워드가 가지는 리스크나 기회 요소에만 집중해서 설명하세요.
            말투는 전문가답고 정중하게 "~습니다/비다." 형태로 작성하세요.
            """

            try:
                insight_desc = self.llm.invoke(prompt).content
            except Exception as e:
                print(f"[Trend AI Error] 인사이트 생성 실패: {e}")
                insight_desc = f"최근 리뷰에서 '{', '.join(keywords)}' 관련 이슈가 {count}건 포착되어 주의가 필요합니다."

            emerging_trends_formatted.append({
                "title": f"주목할 고객 시그널: {trend_title}",
                "desc": insight_desc
            })
            
        return emerging_trends_formatted
    
trend_engine = TrendEngine()