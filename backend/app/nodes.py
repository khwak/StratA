import json
import os
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re
from jinja2 import Environment, FileSystemLoader
import deepl
import time
from sqlalchemy import text

from app.state import AgentState
from app.engines.collector import collector_engine
from app.engines.absa import absa_engine
from app.engines.discovery import discovery_engine
from app.engines.trend import trend_engine
from app.engines.rag import rag_engine
from app.engines.analyst import analyst_engine
from app.engines.strategist import strategist_engine
from app.engines.critic import critic_engine

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from sqlalchemy import create_engine, text
_db_engine = None

# DB 설정 함수
def get_db_engine(url):
    global _db_engine
    if _db_engine is None:
        _db_engine = create_engine(url)
    return _db_engine

# 기간 계산 함수
def calculate_periods(target_period: str):
    trend_periods = []

    if "-Q" in target_period:
        year, q = map(int, target_period.split("-Q"))
        for i in range(5, -1, -1):
            y_diff = i // 4
            q_diff = i % 4
            calc_y = year - y_diff
            calc_q = q - q_diff
            if calc_q <= 0:
                calc_q += 4
                calc_y -= 1
            trend_periods.append(f"{calc_y}-Q{calc_q}")
            
        prev_period = trend_periods[-2] if len(trend_periods) > 1 else target_period
        yoy_period = f"{year-1}-Q{q}"
    else:
        dt = datetime.strptime(target_period, "%Y-%m")
        for i in range(5, -1, -1):
            past_dt = dt - relativedelta(months=i)
            trend_periods.append(past_dt.strftime("%Y-%m"))
            
        prev_period = (dt - relativedelta(months=1)).strftime("%Y-%m")
        yoy_period = (dt - relativedelta(years=1)).strftime("%Y-%m")

    return trend_periods, prev_period, yoy_period

# 번역 헬퍼 함수
def enrich_reviews_with_translation(reviews: list) -> list:
    auth_key = os.environ.get("DEEPL_API_KEY")
    if not auth_key:
        print("[Warning] DeepL API 키가 없습니다. text_en 필드에 원문을 복사합니다.")
        for r in reviews:
            r["text_en"] = r.get("text", "")
        return reviews

    translator = deepl.Translator(auth_key)
    texts_to_translate = [r.get("text", "") for r in reviews]
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            print(f"\n[DeepL] {len(texts_to_translate)}개의 리뷰 번역 중... (시도 {attempt+1}/{max_retries})")
            results = translator.translate_text(texts_to_translate, target_lang="EN-US")
            
            for review, result in zip(reviews, results):
                review["text_en"] = result.text
            print("[DeepL] 번역 완료 및 text_en 필드 추가 성공.")
            return reviews 
                
        except Exception as e:
            print(f"[DeepL Warning] 번역 실패 (시도 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(3) 
            else:
                print("[DeepL Error] 최대 재시도 횟수 초과. 원문을 영문 필드에 복사하여 분석을 강행합니다.")
                for r in reviews:
                    r["text_en"] = r.get("text", "")
                return reviews

# 리포트 파싱 헬퍼 함수
def clean_json_string(s: str) -> str:
    """LLM이 뱉은 마크다운 틱(```json) 및 앞뒤 공백을 안전하게 제거합니다."""
    s = re.sub(r'^```json\s*', '', s, flags=re.MULTILINE)
    s = re.sub(r'^```\s*', '', s, flags=re.MULTILINE)
    return s.strip()


# Node 1: 데이터 수집
def collector_node(state: AgentState) -> AgentState:
    print("\n--- Node 1. 데이터 수집 ---")

    # 분석 기간 설정
    target_period = state.get("target_period", "2026-02")
    analysis_mode = "Quarterly" if "-Q" in target_period else "Monthly"

    # 6개월 시계열 및 비교 기간 자동 계산
    trend_periods, prev_period, yoy_period = calculate_periods(target_period)
    print(f"\n[설정] 모드: {analysis_mode} | 기준: {target_period} | 직전: {prev_period} | 작년: {yoy_period}")
    print(f"[트렌드 기간] {trend_periods}")

    uploaded_reviews = state.get("uploaded_reviews", [])
    uploaded_comp_reviews = state.get("uploaded_comp_reviews", [])
    uploaded_internal_info = state.get("uploaded_internal_info", {})

    # 데이터 수집
    trend_data_dict = {p: [] for p in trend_periods}
    current_data = []
    previous_data = []
    yoy_data = []
    all_raw_reviews = []

    # 업로드된 CSV 데이터가 있는 경우
    if uploaded_reviews:    
        print(f"\n[데이터 수집] 업로드된 자사 리뷰({len(uploaded_reviews)}건)를 사용합니다.")    
        translated_reviews = enrich_reviews_with_translation(uploaded_reviews)
        
        # 날짜(YYYY-MM) 기준으로 데이터 분배 
        for r in translated_reviews:
            r_date = r.get("date", "")
            r_period = r_date[:7] if len(r_date) >= 7 else "" 
            
            if r_period in trend_periods:
                trend_data_dict[r_period].append(r)
            if r_period == target_period:
                current_data.append(r)
            if r_period == prev_period:
                previous_data.append(r)
            if r_period == yoy_period:
                yoy_data.append(r)
                
            all_raw_reviews.append(r)

    # 업로드된 파일이 없는 경우
    else:
        print("\n[데이터 수집] 업로드된 파일이 없습니다. 기존 로컬 데이터를 가져옵니다.")
        for period in trend_periods:
            period_data = collector_engine.fetch_reviews("Internal_Review_API", "my_hotel_reviews.json", period=period)
            period_data = enrich_reviews_with_translation(period_data)
            trend_data_dict[period] = period_data
            all_raw_reviews.extend(period_data)

        current_data = trend_data_dict.get(target_period, [])
        previous_data = trend_data_dict.get(prev_period, [])
        
        yoy_data = collector_engine.fetch_reviews("Internal_Review_API", "my_hotel_reviews.json", period=yoy_period)
        yoy_data = enrich_reviews_with_translation(yoy_data)
        all_raw_reviews.extend(yoy_data)
    
    # 경쟁사 및 기타 정보
    comp_reviews = []
    if uploaded_comp_reviews:
        print(f"[데이터 수집] 업로드된 경쟁사 리뷰({len(uploaded_comp_reviews)}건)를 사용합니다.")
        comp_reviews = enrich_reviews_with_translation(uploaded_comp_reviews)
    else:
        print("[데이터 수집] 업로드된 경쟁사 리뷰가 없습니다. 로컬 더미 데이터를 가져옵니다.")
        comp_reviews = collector_engine.fetch_reviews("Competitor_Aggregator_API", "competitor_reviews.csv", period=target_period)
        comp_reviews = enrich_reviews_with_translation(comp_reviews)
        
    all_raw_reviews.extend(comp_reviews)

    # 자사 정보 처리
    internal_info = {}
    if uploaded_internal_info:
        print("[데이터 수집] 업로드된 자사 내부 정보를 사용합니다.")
        internal_info = uploaded_internal_info
    else:
        print("[데이터 수집] 업로드된 자사 내부 정보가 없습니다. 로컬 더미 데이터를 가져옵니다.")
        internal_info = collector_engine.fetch_internal_info("internal_info.json")


    trends = collector_engine.fetch_external_trends()   

    return {
        "uploaded_reviews": uploaded_reviews,  
        "uploaded_comp_reviews": uploaded_comp_reviews,
        "uploaded_internal_info": uploaded_internal_info,
        "raw_reviews": all_raw_reviews,    
        "current_data": current_data,      
        "previous_data": previous_data,     
        "yoy_data": yoy_data,             
        "trend_data_dict": trend_data_dict, 
        "internal_data": internal_info,
        "competitor_data": {
            "reviews": comp_reviews,
            "trends": trends
        },
        "target_period": target_period,
        "analysis_mode": analysis_mode,
        "feedback_history": state.get("feedback_history", []),
        "current_feedback": state.get("current_feedback", None),
        "feedback_count": state.get("feedback_count", 0)
    }

# Node 2: 정량 분석
def metric_node(state: AgentState) -> AgentState:
    print("\n--- Node 2. 정량 분석 ---")

    # 현재 시점 데이터들
    current_internal = state.get("current_data", [])
    current_comp = state.get("competitor_data", {}).get("reviews", [])

    # 과거 비교군 데이터들
    prev_internal = state.get("previous_data", [])
    yoy_internal = state.get("yoy_data", [])

    trend_data_dict = state.get("trend_data_dict", {})

    print("\nRunning Metric Engine")

    # 6개월 트렌드 데이터 생성
    trend_report = []
    for period, reviews in trend_data_dict.items():
        if reviews:
            metrics = absa_engine.calculate_metrics(reviews)
            scores = metrics.get("scores", {})
            avg_star = round(sum(scores.values()) / len(scores), 2) if scores else None
            if avg_star is not None:
                pos_ratio = int((avg_star / 5.0) * 100)
                neg_ratio = 100 - pos_ratio
            else:
                pos_ratio, neg_ratio = None, None
        else:
            avg_star, pos_ratio, neg_ratio = None, None, None
        
        trend_report.append({
            "month": period[-2:] if "-" in period else period, 
            "star": avg_star,
            "pos": pos_ratio,
            "neg": neg_ratio
        })

    # 현재 자사/경쟁사 지표
    my_metrics = absa_engine.calculate_metrics(current_internal)
    comp_metrics = absa_engine.calculate_metrics(current_comp)
    # 과거 지표
    prev_metrics = absa_engine.calculate_metrics(prev_internal)
    yoy_metrics = absa_engine.calculate_metrics(yoy_internal)

    # 경쟁사와의 격차 및 시계열적 격차 계산
    kpi_gap = absa_engine.calculate_gap(my_metrics, comp_metrics)
    mom_growth = absa_engine.calculate_gap(my_metrics, prev_metrics)
    yoy_growth = absa_engine.calculate_gap(my_metrics, yoy_metrics)

    # 프론트엔드 시각화용 데이터 도출 (Radar, IPA)
    radar_data = absa_engine.calculate_radar(my_metrics, comp_metrics)
    ipa_data = absa_engine.calculate_ipa(my_metrics)

    print("\nRunning Discovery Engine (BERTopic)")
    # 리스크 분석
    my_risks = discovery_engine.discover_risks(current_internal)
    prev_risks = discovery_engine.discover_risks(prev_internal)
    comp_risks = discovery_engine.discover_risks(current_comp)
    unique_risks = discovery_engine.compare_unique_factors(my_risks, comp_risks)
    # 강점 분석
    my_strengths = discovery_engine.discover_strengths(current_internal)
    prev_strengths = discovery_engine.discover_strengths(prev_internal)
    comp_strengths = discovery_engine.discover_strengths(current_comp)
    unique_strengths = discovery_engine.compare_unique_factors(my_strengths, comp_strengths)
    # 트랜드 분석
    my_trends = discovery_engine.discover_trends(current_internal)

    # 프론트엔드 맞춤형 리스크/강점 Top 3 포맷팅 함수
    def format_top_keywords(current_list, prev_list):
        formatted = []
        prev_dict = {item["topic"]: item["count"] for item in prev_list}

        for item in current_list[:3]:
            topic_name = item["topic"]
            current_count = item["count"]
            prev_count = prev_dict.get(topic_name, 0) 
            
            top_2_words = item.get("keywords", [])[:2]
            clean_keywords = ", ".join(top_2_words)

            formatted.append({
                "n": clean_keywords, 
                "v": current_count,
                "up": current_count >= prev_count 
            })
        return formatted

    top_risks = format_top_keywords(my_risks, prev_risks)
    top_strengths = format_top_keywords(my_strengths, prev_strengths)

    external_trends = state.get("competitor_data", {}).get("trends", [])
    emerging_trends_formatted = trend_engine.generate_trend_insights(my_trends, external_trends)

    # 결과 통합 및 구조화
    analysis_result = {
        "period_info": {
            "target": state.get("target_period"),
            "mode": state.get("analysis_mode")
        },
        "kpi_metrics": my_metrics,        
        "competitive_gap": kpi_gap,       
        "growth_metrics": {
            "mom": mom_growth,           
            "yoy": yoy_growth             
        },
        "risks": {
            "current": my_risks,          
            "unique": unique_risks       
        },
        "strengths": {
            "current": my_strengths,      
            "unique": unique_strengths    
        },
        "emerging_trends": my_trends,      
        "visual_data": {                 
            "trend": trend_report,
            "radar": radar_data,
            "ipa": ipa_data,
            "top_risks": top_risks,
            "top_strengths": top_strengths,
            "emerging_trends": emerging_trends_formatted,
            "key_factors": {
                "strengths": [s["n"] for s in top_strengths[:2]] if top_strengths else [],
                "risks": [r["n"] for r in top_risks[:2]] if top_risks else []
            }
        }
    }
    
    print(f"\nUnique Risks: {[r['topic'] for r in unique_risks]}")
    print(f"\nUnique Strengths: {[s['topic'] for s in unique_strengths]}")
    print(f"\nMoM: {mom_growth}")
    print(f"\nYoY: {yoy_growth}")
    
    return {
        "metrics": analysis_result
    }

# Node 3: 근거 확보. RAG Engine
def rag_node(state: AgentState) -> AgentState:
    print("\n--- Node 3. 근거 확보 (RAG) ---")

    metrics = state.get("metrics", {})
    raw_reviews = state.get("raw_reviews", [])

    # DB 연결 확인
    if not rag_engine:
        return {"rag_evidence": ["DB 연결 실패로 검색을 수행할 수 없습니다."]}
    
    rag_engine.index_reviews(raw_reviews)
    search_queries = rag_engine.analyze_outliers(metrics)
    
    mode = metrics.get("period_info", {}).get("mode", "Unknown")
    print(f"\n[RAG] 분석 모드: {mode} | 생성된 쿼리 수: {len(search_queries)}")

    rag_evidence = []
    seen_docs = set()

    # 검색 수행
    if not search_queries:
        rag_evidence.append("특이사항이 없어 추가 검색을 하지 않았습니다.")
    else:
        for query in search_queries:
            found_docs = rag_engine.retrieve_evidence(query)

            if found_docs:
                evidence_block = f"[검색어: {query}]\n"
                added_count = 0
                for doc in found_docs:
                    text = str(doc).strip() 
                    
                    if text not in seen_docs:
                        seen_docs.add(text) 
                        evidence_block += f"    -\"{text}\"\n"
                        added_count += 1
                        
                    if added_count >= 3: 
                        break
                        
                if added_count > 0:
                    rag_evidence.append(evidence_block)
            else:
                rag_evidence.append(f"[검색어: {query}] -> 관련 리뷰 없음")

    # 결과 확인용 로그
    for ev in rag_evidence:
        print(ev.strip())

    return {
        "rag_evidence": rag_evidence
    }

# Node 4: 인사이트 도출. Analyst Agent
def analyst_node(state: AgentState) -> AgentState:    
    metrics = state.get("metrics") or {}
    evidence = state.get("rag_evidence") or {}
    previous_insight = state.get("insight_report") or [] 
    current_feedback = state.get("current_feedback")   
    history = state.get("feedback_history", [])        

    target_period = state.get("target_period", "Unknown")
    analysis_mode = state.get("analysis_mode", "Monthly")

    print(f"\n--- Node 4. 인사이트 도출 (Analyst) | {target_period} ({analysis_mode}) ---")

    final_insight = []

    try:
        if current_feedback and previous_insight:
            target_id = current_feedback.get("target_id")
            user_comment = current_feedback.get("comment")

            print(f"[Feedback]사용자 피드백 반영 중 (ID: {target_id})")

            for item in previous_insight:
                if item["id"] == target_id:
                    old_content = item["content"]
                    revised_content = analyst_engine.revise_insight(
                        target_insight=item, 
                        feedback=user_comment, 
                        metrics=metrics, 
                        evidence=evidence
                    )

                    history.append({
                        "target_id": target_id,
                        "topic": item["topic"],
                        "old_content": old_content,
                        "new_content": revised_content,
                        "feedback": user_comment,
                        "timestamp": target_period
                    })

                    item["content"] = revised_content
                    item["version"] = item.get("version", 1) + 1
                    break

            final_insight = previous_insight
        
        else:
            if not metrics and not evidence:
                print("[Warning] 분석할 데이터가 부족합니다. 기본 결과물을 생성합니다.")
                final_insight = [{
                    "id": "D1", 
                    "topic": "데이터 부족", 
                    "content": "선택하신 기간에 대한 충분한 리뷰 데이터가 확보되지 않아 분석이 제한됩니다.", 
                    "importance": "Low"
                }]
            else:
                print(f"[Analyst] {target_period} 시계열 및 RAG 기반 인사이트 생성 시작...")
                final_insight = analyst_engine.generate_insight(metrics, evidence)
                if not final_insight:
                    raise ValueError("Analyst Engine이 정상적인 데이터를 반환하지 못했습니다.")
    except Exception as e:
        print(f"!!! Analyst Node Error Caught: {e}")
        final_insight = previous_insight if previous_insight else [{
            "id": "ERR_SYS", 
            "topic": "시스템 지연", 
            "content": "데이터 동기화 과정에서 일시적인 지연이 발생했습니다. 다시 시도해 주세요.", 
            "importance": "Medium"
        }]

    return {
        "insight_report": final_insight,
        "feedback_history": history,
        "current_feedback": None,
        "feedback_count": state.get("feedback_count", 0) + 1
    }

# Node 5: 전략 수립 (Strategist Agent)
def strategist_node(state: AgentState) -> AgentState:
    insights = state.get("insight_report", [])
    internal_data = state.get("internal_data", {})
    target_period = state.get("target_period", "Unknown")
    analysis_mode = state.get("analysis_mode", "Monthly")

    print(f"\n--- Node 5. 전략 수립 (Strategist) | {target_period} ({analysis_mode}) ---")    

    db_url = rag_engine.connection
    engine = get_db_engine(db_url)

    user_pref = "일반적인 경영 전략 선호"
    strategy_history = []

    try: 
        with engine.connect() as conn:
            pref_res = conn.execute(text("SELECT pref_style FROM user_preferences ORDER BY id DESC LIMIT 1")).fetchone()
            if pref_res:
                user_pref = pref_res[0]
            hist_res = conn.execute(text("SELECT topic, strategy_name, success_rate FROM strategy_history")).fetchall()
            strategy_history = [
                {"topic": r[0], "strategy": r[1], "success_rate": r[2]} for r in hist_res
            ]
        print(f"DB 데이터 로드 완료 (선호도: {user_pref[:20]}..., 이력: {len(strategy_history)}건)")
    except Exception as e:
        print(f"[DB Warning] DB 로드 중 오류 발생 (기본값 사용): {e}")

    print("MAB 및 사용자 선호도 기반 전략 생성 중...")
    proposal_data = strategist_engine.generate_strategy(
        insights=insights,
        user_prefs=user_pref,
        history=strategy_history,
        internal_data=internal_data,
        period_info={"target": target_period, "mode": analysis_mode}
    )

    return {
        "strategy_proposal": json.dumps(proposal_data, indent=2, ensure_ascii=False),
        "user_preference": user_pref
    }

# Node 6: 검증 (Critic Agent)
def critic_node(state: AgentState) -> AgentState:
    strategy_json = state.get("strategy_proposal")
    insights = state.get("insight_report", [])
    user_pref = state.get("user_preference", "일반 경영 전략 선호")
    internal_data = state.get("internal_data", {})

    target_period = state.get("target_period", "Unknown")
    analysis_mode = state.get("analysis_mode", "Monthly")

    print(f"\n--- Node 6. 검증 및 비평 (Critic) | {target_period} ({analysis_mode}) ---")  

    print("\n[Critic] 전략 리스크 검증 중...")
    critic_result = critic_engine.verify_strategy(
        strategy_proposal=strategy_json,
        insight_report=insights,
        user_pref=user_pref,
        period_info={"target": target_period, "mode":analysis_mode},
        internal_info=internal_data
    )

    # 결과 저장
    final_critique_str = json.dumps(critic_result, indent=2, ensure_ascii=False)
    status_msg = critic_result.get('verification_status', 'N/A')

    print(f"[Critic] 검증 완료 (최종 판정: {status_msg})")

    return {
        "strategy_proposal": f"{strategy_json}\n\n[Critic_Report]\n{final_critique_str}"
    }

# Node 7: 리포트 시각화 (Reporter)
def reporter_node(state: AgentState) -> AgentState:
    print("\n--- Node 7. 최종 리포트 생성 (Reporter) ---")

    metrics = state.get("metrics", {})
    visual_data = metrics.get("visual_data", {})
    
    strategy_str = state.get("strategy_proposal", "")
    
    action_plans = {"shortTerm": [], "longTerm": []}
    critic_feedback = "비평 데이터가 없습니다."

    if "[Critic_Report]" in strategy_str:
        parts = strategy_str.split("[Critic_Report]")
        strat_raw_str = clean_json_string(parts[0])
        critic_raw_str = clean_json_string(parts[1])
        
        # 전략 파싱
        try:
            action_plans = json.loads(strat_raw_str)
        except json.JSONDecodeError as e:
            print(f"[Reporter Warning] JSON 1차 파싱 실패, 정규식 탐색 시도: {e}")
            try:
                strat_match = re.search(r'\{.*\}', strat_raw_str, re.DOTALL)
                if strat_match:
                    action_plans = json.loads(strat_match.group(0))
            except Exception as e2:
                print(f"[Reporter ERROR] 전략 JSON 완전 파싱 실패! 데이터가 유실됩니다: {e2}")
                action_plans = {"shortTerm": [], "longTerm": []}
            
        # 비평 파싱
        try:
            critic_match = re.search(r'\{.*\}', critic_raw_str, re.DOTALL)
            if critic_match:
                critic_data = json.loads(critic_match.group(0))
                critic_feedback = critic_data.get("feedback", "총평 생성 실패")
            else:
                critic_feedback = critic_raw_str
        except Exception:
            critic_feedback = critic_raw_str


    print("\n[Reporter DB] 최종 승인된 전략을 DB(strategy_history)에 기록")
    inserted_count = 0
    try:
        db_url = rag_engine.connection
        engine = get_db_engine(db_url)
        
        with engine.begin() as conn:
            for plan_type in ["shortTerm", "longTerm"]:
                for plan in action_plans.get(plan_type, []):
                    topic = plan.get("topic", "미분류") 
                    strategy_name = plan.get("title", "제목 없음")
                    
                    conn.execute(
                        text("""
                            INSERT INTO strategy_history (topic, strategy_name, success_rate) 
                            VALUES (:topic, :strategy_name, 0.0)
                        """),
                        {"topic": topic, "strategy_name": strategy_name}
                    )
                    inserted_count += 1

        print("[Reporter DB] 전략 기록 완료. (총 {inserted_count}건 INSERT 성공)")
    except Exception as e:
        print(f"[Reporter DB Error] 전략 기록 실패: {e}")

    # Summary 데이터 계산 
    my_scores = metrics.get("kpi_metrics", {}).get("scores", {})
    gap_scores = metrics.get("competitive_gap", {})
    
    avg_kpi = round(sum(my_scores.values()) / len(my_scores), 1) if my_scores else 0
    avg_gap = round(sum(gap_scores.values()) / len(gap_scores), 1) if gap_scores else 0
    
    if avg_gap >= 0.5: summary_level = "우수 (경쟁 우위)"
    elif avg_gap >= -0.5: summary_level = "보통 (시장 평균)"
    else: summary_level = "주의 (경쟁 열위)"

    # 최종 프론트엔드 전달용 JSON 스키마
    final_report = {
        "trend": visual_data.get("trend", []),
        "radar": visual_data.get("radar", []),
        "summary": {
            "kpi": avg_kpi,
            "gap": avg_gap,
            "level": summary_level
        },
        "ipa": visual_data.get("ipa", []),
        "action_plans": action_plans,
        "critic_feedback": critic_feedback,
        
        "top_risks": visual_data.get("top_risks", []),
        "top_strengths": visual_data.get("top_strengths", []),
        "emerging_trends": visual_data.get("emerging_trends", []),
        "key_factors": visual_data.get("key_factors", {"strengths": [], "risks": []}),
        
        "detailed_metrics": {
            "period_info": metrics.get("period_info", {}),
            "kpi_metrics": metrics.get("kpi_metrics", {}).get("scores", {}), 
            "competitive_gap": metrics.get("competitive_gap", {}),
            "growth_metrics": metrics.get("growth_metrics", {})
        }
    }

    # 마크다운 렌더링
    try:
        current_dir = os.path.dirname(__file__)
        env = Environment(loader=FileSystemLoader(current_dir))
        template = env.get_template('report_template.md')
        
        md_report = template.render(**final_report)
        final_report["markdown_report"] = md_report
    except Exception as e:
        print(f"\n[Reporter Error] Jinja2 템플릿 렌더링 실패: {e}")
        final_report["markdown_report"] = "마크다운 리포트 생성 중 오류가 발생했습니다."

    print("\n[Reporter] 프론트엔드용 리포트 구성 완료.")
    
    return {
        "final_report": final_report
    }