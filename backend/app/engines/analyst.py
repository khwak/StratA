import os
import json
from typing import List, Optional 
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

class InsightItem(BaseModel):
    id: int = Field(description="인사이트 고유 번호")
    topic: str = Field(description="분석 주제 (예: 서비스 품질, 경쟁사 대응 등)")
    analysis_type: str = Field(description="분석 유형: Known(기존 인지), New(새로운 발견), Check(확인 필요)")
    content: str = Field(description="상세 분석 내용 및 근거")
    criticality: str = Field(description="중요도: High, Medium, Low")
    evidence_quotes: List[str] = Field(default=[], description="분석의 근거가 된 실제 고객 리뷰 문장들을 RAG 데이터에서 추출하여 포함")
    version: int = Field(default=1, description="수정 버전")

class InsightList(BaseModel):
    insights: List[InsightItem] = Field(description="도출된 인사이트 항목 리스트")

class AnalystEngine:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, max_retries=3, timeout=30)
        self.parser = JsonOutputParser(pydantic_object=InsightList)

    def generate_insight(self, metrics: dict, evidence: list) -> List[dict]:
        system_prompt = """
        당신은 호텔 경영 전략 전문 컨설턴트입니다. 
        제공된 [지표 데이터]와 [RAG 근거]를 분석하여 경영진 보고용 인사이트를 도출하세요.

        분석 핵심 지침:
        1. [추세 분석]: growth_metrics(MoM, YoY)를 확인하여 지표의 상승/하락 폭을 정확히 언급하세요. 
        2. [원인 규명]: RAG 근거(리뷰 원문)를 통해 지표 변화의 구체적인 '이유'를 찾으세요. 
        3. [근거 매핑]: 각 인사이트마다 이를 뒷받침하는 실제 리뷰 문장을 2~3개씩 반드시 추출하여 'evidence_quotes' 필드에 넣으세요.
        4. [중요도 산출]: 
        - High: 전월/전년 대비 하락폭이 크거나(-2.0 이상), 경쟁사보다 점수가 낮은 경우.
        - Medium: 지표의 소폭 하락이나 새로운 불편 사항이 감지된 경우.
        - Low: 지표는 양호하나 개선 제안이 있는 경우.
        5. [사고 체계]: Known(반복 문제), New(돌발 이슈), Check(확인 필요 가설)를 구분하세요.
        """

        user_prompt = """
        [데이터 정보]
        - 분석 대상 및 모드: {period_info}
        - 현재 KPI 및 경쟁사 격차: {kpi_metrics} / {gap}
        - 시계열 변화율 (MoM/YoY): {growth}
        - 발견된 리스크 및 트렌드 토픽: {risks_trends}
        - 고객 리뷰 원문 근거(RAG): {evidence}

        [지시 사항]
        - 각 인사이트의 'content'는 수치와 근거를 포함하여 2~3문장으로 전문적으로 작성하세요.
        - 'evidence_quotes'에는 {evidence} 리스트에서 해당 인사이트와 직접적으로 관련된 문장을 그대로 인용하세요.
        - 결과는 지정된 JSON Schema 형식을 엄격히 준수하세요.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("system", "{format_instructions}"),
            ("user", user_prompt)
        ])

        chain = prompt | self.llm | self.parser

        try:
            response = chain.invoke({
                "period_info": json.dumps(metrics.get("period_info", {}), ensure_ascii=False),
                "kpi_metrics": json.dumps(metrics.get("kpi_metrics", {}), ensure_ascii=False),
                "gap": json.dumps(metrics.get("competitive_gap", {}), ensure_ascii=False),
                "growth": json.dumps(metrics.get("growth_metrics", {}), ensure_ascii=False),
                "risks_trends": f"Risks: {metrics.get('risks')}, Trends: {metrics.get('emerging_trends')}",
                "evidence": "\n".join(evidence),
                "format_instructions": self.parser.get_format_instructions()
            })
            return response.get("insights", [])
        except Exception as e:
            print(f"Analyst Engine Error: {e}")
            return []

    def revise_insight(self, target_insight: dict, feedback: str, metrics: dict, evidence: list) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 사용자의 피드백과 시계열 데이터를 바탕으로 분석 보고서를 수정하는 전문가입니다."),
            ("user", """
             [원본 분석 항목]
             주제: {topic}
             내용: {old_content}

             [사용자 피드백]
             {feedback}

             [참고 데이터]
             - 시계열 지표(MoM/YoY): {growth}
             - 현재 지표: {kpi}
             - RAG 근거: {evidence}

             지시사항:
             1. 피드백이 지표 변화 추이(MoM/YoY)와 일치하는지 확인하여 논리적으로 재구성하세요.
             2. 수정된 '내용(content)' 문자열만 반환하세요. 다른 설명은 생략하세요.
            """)
        ])

        chain = prompt | self.llm
        
        try:
            response = chain.invoke({
                "topic": target_insight.get("topic", "N/A"),
                "old_content": target_insight.get("content", "N/A"),
                "feedback": feedback,
                "growth": json.dumps(metrics.get("growth_metrics", {}), ensure_ascii=False),
                "kpi": json.dumps(metrics.get("kpi_metrics", {}), ensure_ascii=False),
                "evidence": "\n".join(evidence)
            })
            return response.content.strip()
        except Exception as e:
            print(f"Insight Revision Error: {e}")
            return target_insight.get("content", "내용 수정 중 오류가 발생했습니다.")
    
analyst_engine = AnalystEngine()