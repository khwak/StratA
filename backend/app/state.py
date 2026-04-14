from typing import TypedDict, List, Dict, Optional, Any

class AgentState(TypedDict):
    # 업로드된 CSV 파싱 데이터
    uploaded_reviews: List[Dict[str, Any]]        # 시트 1: 자사 리뷰
    uploaded_comp_reviews: List[Dict[str, Any]]   # 시트 2: 경쟁사 리뷰
    uploaded_internal_info: Dict[str, Any]        # 시트 3: 자사 내부 정보

    # 초기 입력 데이터
    raw_reviews: List[str]    # 리뷰 리스트
    internal_data: dict       # 자사 데이터
    competitor_data: dict     # 경쟁사 데이터
    target_period: str        # 분석 대상 기간
    analysis_mode: str        # "Monthly" 또는 "Quarterly"

    # 분석을 위한 데이터셋
    current_data: List[Dict[str, Any]]                 # 현재 기간
    previous_data: List[Dict[str, Any]]                # 직전 기간 (MoM/QoQ)
    yoy_data: List[Dict[str, Any]]                     # 작년 동일 기간 (YoY)
    trend_data_dict: Dict[str, List[Dict[str, Any]]]   # 6개월 연속 트렌드 데이터 저장용

    # 분석 중간 결과
    metrics: dict             # 정량 분석 결과
    rag_evidence: List[str]   # 검색된 근거 자료

    # 에이전트 산출물
    insight_report: List[Dict[str, Any]]        # 인사이트 추출 결과
    strategy_proposal: str                      # 전략 수립 결과

    # 최종 결과물
    final_report: dict        # 프론트엔드 전송용

    # 피드백용
    current_feedback: Optional[Dict[str, Any]]  # 사용자가 입력한 피드백
    feedback_history: List[Dict[str, Any]]      # 피드백 맥락 저장용 리스트
    user_preference: str                        # 사용자 선호도

    # 제어용
    feedback_count: int       # 루프 제한용 카운터

    # 에러 처리용
    error: Optional[str]