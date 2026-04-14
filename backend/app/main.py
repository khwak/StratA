from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, text
import os
import json
import uuid
import uvicorn
import csv
import io
import pandas as pd

from app.graph import app_graph

DB_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg://user:password@db:5432/strata_db")
db_engine = create_engine(DB_URL)
app = FastAPI(title="StratA API Server")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청 데이터 모델
#class InitRequest(BaseModel):
#    thread_id: Optional[str] = None    # 세션 ID
#    target_period: str = Field(default="2026-02", description="분석 대상 기간 (예: 2026-02 또는 2026-Q1)")
#    analysis_mode: str = Field(default="Monthly", description="Monthly 또는 Quarterly")

class FeedbackRequest(BaseModel):
    thread_id: str
    target_id: int   
    comment: str      

class ConfirmRequest(BaseModel):
    thread_id: str

async def get_current_state(config: dict):
    state_snapshot = app_graph.get_state(config)
    current_values = state_snapshot.values

    next_node = state_snapshot.next

    return {
        "thread_id": config["configurable"]["thread_id"],
        "next_step": next_node,
        "target_period": current_values.get("target_period"),    
        "metrics": current_values.get("metrics", {}),
        "insights": current_values.get("insight_report", []),   
        "final_report": current_values.get("final_report", {})  
    }

# 시작
@app.post("/init")
async def start_analysis(
    thread_id: Optional[str] = Form(None),
    target_period: str = Form("2026-02"),
    analysis_mode: str = Form("Monthly"),
    file: Optional[UploadFile] = File(None)
    ):

    thread_id = thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\n[API] 분석 시작 (대상 기간: {target_period} | Thread ID: {thread_id})")

    uploaded_reviews = []
    uploaded_comp_reviews = []
    uploaded_internal_info = {}

    if file and file.filename.endswith(('.xlsx', '.xls')):
        content = await file.read()
        df_dict = pd.read_excel(io.BytesIO(content), sheet_name=None)
        
        if 'My_Reviews' in df_dict:
            df_my = df_dict['My_Reviews'].fillna("")
            uploaded_reviews = df_my.to_dict('records')
            
        if 'Comp_Reviews' in df_dict:
            df_comp = df_dict['Comp_Reviews'].fillna("")
            uploaded_comp_reviews = df_comp.to_dict('records')
            
        if 'Internal_Info' in df_dict:
            df_info = df_dict['Internal_Info'].fillna("")
            for _, row in df_info.iterrows():
                if 'Key' in row and 'Value' in row:
                    uploaded_internal_info[row['Key']] = row['Value']

        print(f"[API] 엑셀 파싱 완료: 자사({len(uploaded_reviews)}건), 경쟁사({len(uploaded_comp_reviews)}건)")

    initial_state = {
        "target_period": target_period,
        "analysis_mode": analysis_mode,
        "uploaded_reviews": uploaded_reviews,
        "uploaded_comp_reviews": uploaded_comp_reviews,
        "uploaded_internal_info": uploaded_internal_info
    }
    async def event_generator():
        current_node = "startup" 
        try:
            async for event in app_graph.astream(initial_state, config=config, stream_mode="updates"):
                for node_name in event.keys():
                    current_node = node_name
                    yield f"{json.dumps({'type': 'progress', 'node': node_name})}\n"
                    
            final_state = await get_current_state(config)
            yield f"{json.dumps({'type': 'complete', 'data': final_state})}\n"
            
        except Exception as e:
            print(f"[API Stream Error] Node '{current_node}' failed: {e}")
            error_msg = f"'{current_node}' 단계 처리 중 오류가 발생했습니다. (상세: {str(e)})"
            yield f"{json.dumps({'type': 'error', 'message': error_msg, 'node': current_node})}\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

# 피드백 수용
@app.post("/feedback")
async def send_feedback(req: FeedbackRequest):
    config = {"configurable": {"thread_id": req.thread_id}}

    print(f"\n[API] 피드백 수신: ID {req.target_id} -> {req.comment}")


    try:
        with db_engine.begin() as conn:
            positive_keywords = ["좋아", "반영", "훌륭", "동의", "완벽", "그대로", "유지"]
            if any(kw in req.comment for kw in positive_keywords):
                conn.execute(text("""
                    UPDATE strategy_history 
                    SET success_rate = success_rate + 0.1 
                    WHERE id IN (SELECT id FROM strategy_history ORDER BY id DESC LIMIT 3)
                """))
                print("[API DB] 긍정적 피드백 감지: 최근 전략 success_rate 가산 완료")

            conn.execute(text("""
                UPDATE user_preferences 
                SET pref_style = pref_style || ' | 새로운 피드백: ' || :comment 
                WHERE id = (SELECT MAX(id) FROM user_preferences)
            """), {"comment": req.comment})
            print("[API DB] 사용자 선호도 업데이트 완료")

    except Exception as e:
        print(f"[API DB Error] 피드백 DB 업데이트 실패: {e}")


    app_graph.update_state(
        config,
        {"current_feedback": {"target_id": req.target_id, "comment": req.comment}},
        as_node="rag"
    )
    
    await app_graph.ainvoke(None, config=config)  

    return await get_current_state(config)

# 승인 및 최종 완료
@app.post("/confirm")
async def confirm_analysis(req: ConfirmRequest):
    config = {"configurable": {"thread_id": req.thread_id}}

    print(f"\n[API] 인사이트 승인. 전략 수립 진행. (Thread ID: {req.thread_id})")
    app_graph.update_state(
        config,
        {},
        as_node="analyst" 
    )

    async def event_generator():
        current_node = "analyst (재개)"
        try:
            async for event in app_graph.astream(None, config=config, stream_mode="updates"):
                for node_name in event.keys():
                    current_node = node_name
                    yield f"{json.dumps({'type': 'progress', 'node': node_name})}\n"

            final_state = await get_current_state(config)
            yield f"{json.dumps({'type': 'complete', 'data': final_state})}\n"
            
        except Exception as e:
            print(f"[API Stream Error] Node '{current_node}' failed: {e}")
            error_msg = f"'{current_node}' 단계 처리 중 오류가 발생했습니다. (상세: {str(e)})"
            yield f"{json.dumps({'type': 'error', 'message': error_msg, 'node': current_node})}\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)