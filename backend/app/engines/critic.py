import json
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# 개별 전략에 대한 비평 항목 스키마
class StrategyCritique(BaseModel):
    target_strategy_name: str = Field(description="평가 대상 전략 명칭")
    strategic_alignment: str = Field(description="현재 호텔의 강점/약점과의 부합성")
    expected_impact: str = Field(description="실행 시 예상되는 긍정적 비즈니스 임팩트")
    improvement_suggestion: str = Field(description="실행력을 더 높이기 위한 건설적인 보완 제안")
    risk_score: int = Field(description="실행 난이도 및 리스크 점수 (1-10, 높을수록 실행이 까다로움)")

# 전체 비평 리포트 스키마
class CriticReport(BaseModel):
    critiques: List[StrategyCritique]
    verification_status: str = Field(description="최종 상태: Approved / Needs Minor Tweaks / Fail")
    feedback: str = Field(description="""AI 종합 총평 (CSO 관점의 Executive Summary). 반드시 1) 데이터로 확인된 현재 호텔의 핵심 장점/경쟁력, 2) 가장 시급하게 집중해야 할 핵심 개선점, 3) 제안된 전략에 대한 종합 의견을 포함하여 전문가적이고 정중한 줄글(또는 가독성 좋은 불릿 형태)로 작성.""")


class CriticEngine:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, max_retries=3, timeout=30)
        self.structured_llm = self.llm.with_structured_output(CriticReport)

    def verify_strategy(self, strategy_proposal: str, insight_report: List[Dict], user_pref: str, period_info: Dict, internal_info: dict = None) -> Dict:
        if internal_info is None:
            print("[Critic Node Error] no internal data.")
            internal_info = {}

        system_prompt = """
        당신은 글로벌 호텔 체인의 최고전략책임자(CSO)이자 비즈니스 컨설턴트입니다.
        데이터(인사이트)와 제안된 전략, 그리고 호텔의 실제 내부 정보({internal_info_str})를 종합하여 명확하고 통찰력 있는 'AI 종합 분석 총평(Executive Summary)'을 작성하세요.

        [총평(Feedback) 작성 가이드라인]
        1. [진짜 핵심 경쟁력 강조]: "개선하면 좋아진다" 같은 추상적인 소리는 절대 하지 마십시오. 
           반드시 {internal_info_str}에 명시된 자사 호텔만의 시설, 서비스 특징이나, 리뷰 데이터 상에서 고객들이 칭찬한 구체적인 요소(예: 수영장 시설, 조식 퀄리티 등)를 '가장 강력한 장점'으로 짚어주세요.
        2. [시급한 개선점 타겟팅]: 수많은 리스크 중 경영진이 가장 먼저 해결해야 할 '가장 시급한 개선점' 1가지를 선정하고 그 이유를 설명하세요.
        3. [전략적 방향성 평가]: 제안된 전략이 앞서 언급한 장점을 극대화하고 약점을 보완하는 데 적절한지 평가하세요.
        """

        user_prompt = """
        [검증 대상 데이터]
        - 현재 분석 기간: {period_info}
        - 자사 호텔 내부 정보: {internal_info_str} 
        - 제안된 전략서: {strategy_proposal}
        - 근거 인사이트: {insight_report}
        - 사용자 경영 선호도: {user_pref}
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])

        chain = prompt | self.structured_llm

        try:
            result = chain.invoke({
                "strategy_proposal": strategy_proposal,
                "insight_report": insight_report,
                "user_pref": user_pref,
                "period_info": json.dumps(period_info, ensure_ascii=False),
                "internal_info_str": json.dumps(internal_info, ensure_ascii=False)
            })
            return result.model_dump()
        except Exception as e:
            print(f"Critic Engine Error: {e}")
            return {
                "critiques": [], 
                "verification_status": "Fail", 
                "feedback": "AI 총평을 생성하는 중 오류가 발생했습니다. 전략 데이터를 다시 확인해주세요."
            }
        
critic_engine = CriticEngine()