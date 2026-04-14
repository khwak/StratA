from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.state import AgentState
from app.nodes import (
    collector_node,
    metric_node,
    rag_node,
    analyst_node,
    strategist_node,
    critic_node,
    reporter_node
)

# 그래프 생성
workflow = StateGraph(AgentState)

# 노드 등록
workflow.add_node("collector", collector_node)
workflow.add_node("metric", metric_node)
workflow.add_node("rag", rag_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("strategist", strategist_node)
workflow.add_node("critic", critic_node)
workflow.add_node("reporter", reporter_node)

# 엣지 연결
workflow.add_edge(START, "collector")
workflow.add_edge("collector", "metric")
workflow.add_edge("metric", "rag")
workflow.add_edge("rag", "analyst")

workflow.add_edge("analyst", "strategist")  
workflow.add_edge("strategist", "critic")
workflow.add_edge("critic", "reporter")
workflow.add_edge("reporter", END)

# 체크포인트 설정
memory = MemorySaver()

# 그래프 컴파일
app_graph = workflow.compile(
    checkpointer=memory,
    interrupt_after=["analyst"]
)