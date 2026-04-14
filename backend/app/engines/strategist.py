import json
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class ActionPlanItem(BaseModel):
    topic: str = Field(description="이 전략이 타겟팅하는 핵심 주제/키워드 (예: 청결, 서비스, 시설, 가격, 마케팅 등)")
    title: str = Field(description="전략의 핵심 제목 (예: 1. 청결 리스크 긴급 안정화)")
    details: List[str] = Field(description="실행 가능한 구체적인 액션 아이템 목록 (문장형)")
    expected_effect: str = Field(description="기대 효과 및 목표 지표")
    estimated_resource: str = Field(description="예상 비용 및 투입 노력 (예: 낮음/보통/높음)")
    mab_reasoning: str = Field(description="이 전략이 선택된 이유 (MAB/선호도 기반)")

class StrategyProposal(BaseModel):
    shortTerm: List[ActionPlanItem] = Field(description="즉시 실행 가능한 Quick Win 단기 전략")
    longTerm: List[ActionPlanItem] = Field(description="구조적 체질 개선을 위한 장기 전략")
    priority_actions: List[str] = Field(description="즉시 실행해야 할 우선순위 과제 리스트")

class StrategistEngine:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4, max_retries=3, timeout=30)
        self.structured_llm = self.llm.with_structured_output(StrategyProposal)

    def generate_strategy(
            self,
            insights: List[Dict],
            user_prefs: str,
            history: List[Dict],
            internal_data: Dict,
            period_info: Dict
    ) -> Dict:
        system_prompt = """
        당신은 호텔 총지배인(GM) 출신의 전략 컨설턴트입니다. 
        분석가(Analyst)의 인사이트와 시계열 지표를 바탕으로 실행 가능한 전략을 수립하세요.

        [전략 수립 원칙]
        1. [시계열 대응]: MoM/YoY 지표가 급락한 항목은 '복구(Recovery)' 전략을, 상승한 항목은 '강화(Reinforcement)' 전략을 세우십시오.
        2. [MAB 기반 선택]: 과거 성공 사례({history})가 있는 방식(Exploitation)을 우선하되, 새로운 위협(New Insight)에는 혁신적 대안(Exploration)을 제안하세요.
        3. [리소스 정합성]: 호텔의 실제 시설 및 사양({internal_data}) 내에서 실행 가능한 계획만 제안하십시오.
        4. [톤앤매너]: 사용자의 경영 스타일 선호도({user_prefs})에 부합하도록 작성하십시오.

        [중요 제약 사항: 환각(Hallucination) 방지]
        제공된 과거 이력(history) 데이터가 비어있거나 부족하다면, 절대 과거 사례를 임의로 지어내지 마십시오. 
        이 경우 'mab_reasoning'에 "누적된 과거 데이터가 없어 보편적인 호스피탈리티 산업의 베스트 프랙티스에 근거함"이라고 명확히 기술하고, 그에 기반하여 전략을 추론하십시오.
        """
        
        user_prompt = """
        [데이터 요약]
        - 분석 기간 및 모드: {period_info}
        - 도출된 인사이트: {insights}
        - 과거 전략 성과 히스토리: {history}

        [지시 사항]
        - 'Quick Win'은 즉시 지표 개선이 가능한 조치, 'Long-term'은 구조적 체질 개선을 의미합니다.
        - 'mab_reasoning'에는 왜 이 전략이 과거 이력이나 현재 지표 하락세에 비추어 최적인지 기술하십시오.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])

        chain = prompt | self.structured_llm

        try: 
            result = chain.invoke({
                "insights": json.dumps(insights, ensure_ascii=False),
                "user_prefs": user_prefs,
                "history": json.dumps(history, ensure_ascii=False),
                "internal_data": json.dumps(internal_data, ensure_ascii=False),
                "period_info": json.dumps(period_info, ensure_ascii=False)
            })
            return result.model_dump()
        except Exception as e:
            print(f"Strategist Engine Error: {e}")
            return {"shortTerm": [], "longTerm": [], "priority_actions": []}

strategist_engine = StrategistEngine()