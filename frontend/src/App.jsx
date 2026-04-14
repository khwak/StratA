import { useState } from 'react';
import { strataApi } from './api/strata';
import LoadingOverlay from './components/LoadingOverlay';
import FeedbackView from './components/FeedbackView'; 
import VisualReportView from './components/report/VisualReportView'; 
import ReportNavigation from './components/ReportNavigation';

function App() {
  const [mode, setMode] = useState("Monthly");
  const [period, setPeriod] = useState("2026-02");
  const [loading, setLoading] = useState(false);
  const [loadingType, setLoadingType] = useState("init"); // "init" 또는 "confirm"
  const [data, setData] = useState(null);
  const [viewMode, setViewMode] = useState("feedback");  // "feedback" | "report"
  const [selectedFile, setSelectedFile] = useState(null);
  const [streamMessage, setStreamMessage] = useState("");

  // 1. 분석 시작 (Initial Analysis)
  const handleStartAnalysis = async () => {
    setLoadingType("init");
    setLoading(true);
    setStreamMessage("데이터 준비 및 파이프라인 가동 중..."); 

    try {
      let finalData = null;
      let hasError = false;

      await strataApi.initStream(period, mode, selectedFile, (messageChunk) => {
        if (messageChunk.type === 'error') {
          hasError = true;
          alert(`분석 중 시스템 오류가 발생했습니다.\n\n에러 내용: ${messageChunk.message}`);
          return;
        }

        if (messageChunk.type === 'progress') {
          const nodeMessages = {
            'collector': "데이터 수집 진행 중...",
            'metric': "감성 및 지표 분석 중...",
            'rag': "RAG 기반 근거 확보 중...",
            'analyst': "보고서 작성 중..."
          };
          
          if (nodeMessages[messageChunk.node]) {
            setStreamMessage(nodeMessages[messageChunk.node]);
          }
        } else if (messageChunk.type === 'complete') {
          finalData = messageChunk.data;
        }
      });

      if (!hasError && finalData) {
        setData(finalData);
      }
    } catch (error) {
      alert("분석 시작 중 서버와 연결이 끊어졌습니다.");
    } finally {
      setLoading(false);
      setStreamMessage(""); 
    }
  };

  // 2. 피드백 전송 (Insight Feedback)
  const handleUpdateInsight = async (threadId, targetId, comment) => {
    try {
      const res = await strataApi.sendFeedback(threadId, targetId, comment);
      setData(res.data); 
    } catch (err) {
      alert("피드백 반영 실패");
    }
  };

  // 3. 최종 승인 및 전략 수립 (Confirm & Strategy)
  const handleConfirmAnalysis = async () => {
    setLoadingType("confirm"); 
    setLoading(true);
    setStreamMessage("인사이트 승인 및 전략 수립 준비 중..."); 

    try {
      let finalData = null;
      let hasError = false;

      await strataApi.confirmStream(data.thread_id, (messageChunk) => {
        if (messageChunk.type === 'error') {
          hasError = true;
          alert(`전략 수립 중 에이전트 오류가 발생했습니다.\n\n에러 내용: ${messageChunk.message}`);
          return;
        }
        if (messageChunk.type === 'progress') {
          const nodeMessages = {
            'strategist': "사용자 선호도 기반 행동 계획 생성 중...",
            'critic': "전략 리스크 검증 및 비평 진행 중...",
            'reporter': "최종 경영 전략 마크다운 리포트 구성 중..."
          };
          
          if (nodeMessages[messageChunk.node]) {
            setStreamMessage(nodeMessages[messageChunk.node]);
          }
        } else if (messageChunk.type === 'complete') {
          finalData = messageChunk.data;
        }
      });

      if (!hasError && finalData) {
        setData(finalData); 
        setViewMode("report"); 
      }
    } catch (error) {
      alert("전략 수립 중 에이전트 오류가 발생했습니다.");
    } finally {
      setLoading(false);
      setStreamMessage(""); 
    }
  };

  const handleGoHome = () => {
    setViewMode("feedback");
    setData(null); // 데이터 초기화가 필요한 경우
    setSelectedFile(null);
    window.location.reload(); 
  };

  const handleDownloadMarkdown = () => {
    const markdownText = data?.final_report?.markdown_report;
    if (!markdownText) {
      alert("다운로드할 마크다운 리포트 데이터가 없습니다.");
      return;
    }
    const blob = new Blob([markdownText], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `StratA_Insight_Report_${period}.md`; // 기간별 파일명 지정
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* 로딩 타입에 따라 메시지가 달라지는 오버레이 */}
      {loading && <LoadingOverlay type={loadingType} customMessage={streamMessage} />}
      
      {/* 전략 보고서가 생성된 경우에만 내비게이션 바 표시 */}
      {viewMode === "report" && <ReportNavigation />}
      
      <header className="bg-white border-b sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 h-20 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">StratA Dash</h1>
            <p className="text-xs text-slate-400 font-medium">AI-Agent Insight Service</p>
          </div>
          <div className="flex items-center gap-4">
            {viewMode === "feedback" ? (
              <>
            <div className="flex bg-slate-100 p-1 rounded-lg border border-slate-200">
              <button 
                onClick={() => { setMode("Monthly"); setPeriod("2026-02"); }}
                className={`px-3 py-1.5 text-xs font-bold rounded-md transition-all ${mode === 'Monthly' ? 'bg-white shadow-sm text-blue-600' : 'text-slate-400'}`}
              >
                월별
              </button>
              <button 
                onClick={() => { setMode("Quarterly"); setPeriod("2026-Q1"); }}
                className={`px-3 py-1.5 text-xs font-bold rounded-md transition-all ${mode === 'Quarterly' ? 'bg-white shadow-sm text-blue-600' : 'text-slate-400'}`}
              >
                분기별
              </button>
            </div>

            <input 
              type="text" 
              value={period} 
              onChange={(e) => setPeriod(e.target.value)} 
              className="border rounded-lg px-3 py-2 text-sm w-28 bg-slate-50 font-bold text-center"
            />

            <input 
              type="file" 
              accept=".xlsx, .xls"
              onChange={(e) => setSelectedFile(e.target.files[0])}
              className="border border-slate-200 rounded-lg pl-2 py-1 text-sm w-56 bg-slate-50 text-slate-600 font-medium 
                file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 
                file:text-xs file:font-bold file:bg-blue-100 file:text-blue-700 
                hover:file:bg-blue-200 transition-all cursor-pointer file:cursor-pointer"
            />
            
            <button 
              onClick={handleStartAnalysis}
              disabled={loading}
              className={`
                px-6 py-2 rounded-lg text-sm font-bold transition-all duration-200 shadow-lg
                ${loading 
                  ? 'bg-slate-400 text-slate-100 cursor-not-allowed' 
                  : 'bg-blue-600 text-white hover:bg-blue-700 hover:shadow-blue-200 active:scale-95 shadow-blue-100'
                }
              `}
            >
              {loading && loadingType === "init" ? (
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  분석 중...
                </div>
              ) : (
                "분석 시작"
              )}
            </button>
            </>
            ) : (
              <div className="flex gap-2">
                <button 
                  onClick={handleDownloadMarkdown} 
                  className="px-6 py-2 rounded-lg text-sm font-bold bg-slate-800 text-white shadow-lg shadow-slate-200 hover:bg-slate-900 transition-all flex items-center gap-2"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                  MD 다운로드
                </button>
                <button 
                  onClick={handleGoHome} 
                  className="px-6 py-2 rounded-lg text-sm font-bold bg-blue-600 text-white shadow-lg shadow-blue-100 hover:bg-blue-700 transition-all"
                >
                  홈으로
                </button>
              </div>
            )}
            
            

          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10">
        {viewMode === "feedback" ? (
          <FeedbackView 
            data={data} 
            onUpdate={handleUpdateInsight} 
            onConfirm={handleConfirmAnalysis} 
          />
        ) : (
          <VisualReportView data={data} />
        )}
      </main>
    </div>
  );
}

export default App;