import { useState } from 'react';
import { ChevronDown, ChevronUp, MessageSquare, Database } from 'lucide-react';

const InsightCard = ({ insight, threadId, onUpdate }) => {
  const [showFeedback, setShowFeedback] = useState(false);
  const [showEvidence, setShowEvidence] = useState(false); 
  const [comment, setComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const criticalityMap = {
    High: { bg: "bg-red-100", text: "text-red-700", label: "매우 높음" },
    Medium: { bg: "bg-amber-100", text: "text-amber-700", label: "보통" },
    Low: { bg: "bg-emerald-100", text: "text-emerald-700", label: "낮음" },
  };

  const currentStatus = criticalityMap[insight.criticality] || criticalityMap.Medium;

  const handleCardToggle = () => {
    setShowFeedback(!showFeedback);
    setShowEvidence(false); 
  };

  const handleEvidenceToggle = (e) => {
    e.stopPropagation();
    setShowEvidence(!showEvidence);
  };

  const stopPropagation = (e) => {
    e.stopPropagation();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!comment.trim()) return;
    setIsSubmitting(true);
    try {
      await onUpdate(threadId, insight.id, comment);
      setComment("");
      setShowFeedback(false);
    } catch (error) {
      console.error("피드백 업데이트 실패:", error);
      alert("피드백 전송에 실패했습니다. 다시 시도해주세요."); 
    } finally {
      setIsSubmitting(false); 
    }
  };

  return (
    <div className="relative bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden mb-4 transition-all hover:border-blue-300">
      {/* 카드 전용 로딩 오버레이 */}
      {isSubmitting && (
        <div className="absolute inset-0 bg-white/70 backdrop-blur-[1px] z-10 flex flex-col items-center justify-center">
          <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-2"></div>
          <span className="text-xs font-bold text-blue-600">피드백 반영 중..</span>
        </div>
      )}
      {/* 카드 상단: 클릭 시 피드백 창 토글 및 근거 창 닫기 */}
      <div className="p-5 cursor-pointer" onClick={handleCardToggle}>
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-2">
            <span className="text-lg font-black text-slate-300">#{insight.id}</span>
            <h3 className="font-bold text-lg text-slate-800">{insight.topic}</h3>
          </div>
          <div className={`flex flex-col items-end`}>
            <span className="text-[10px] font-bold text-slate-400 mb-1">분석 중요도</span>
            <span className={`${currentStatus.bg} ${currentStatus.text} px-2 py-1 rounded text-xs font-black uppercase`}>
              {currentStatus.label}
            </span>
          </div>
        </div>
        
        <p className="text-slate-600 text-sm leading-relaxed">{insight.content}</p>
        
        <div className="mt-4 flex gap-4" onClick={stopPropagation}>
          <button 
            type="button"
            onClick={handleEvidenceToggle}
            className="flex items-center gap-1.5 text-xs font-bold text-blue-600 hover:text-blue-800 hover:underline transition-colors cursor-pointer"
          >
            <Database size={14} /> {showEvidence ? "분석 근거(RAG) 닫기" : "분석 근거(RAG) 보기"}
            {showEvidence ? <ChevronUp size={14} /> : <ChevronDown size={14} /> }
          </button>
          <button 
            type="button"
            onClick={handleCardToggle}
            className={`flex items-center gap-1.5 text-xs font-bold transition-colors ${showFeedback ? "text-blue-600" : "text-slate-400 hover:text-slate-600"}`}
          >
            <MessageSquare size={14} /> {showFeedback ? "피드백 접기" : "클릭하여 피드백"}
          </button>
        </div>
      </div>

      {/* RAG 근거 영역 (토글) */}
      {showEvidence && (
        <div className="bg-slate-50 px-5 py-4 border-t border-slate-100 animate-in fade-in slide-in-from-top-1">
          <h4 className="text-[11px] font-black text-slate-400 uppercase mb-3 flex items-center gap-1">
            <Database size={12} /> AI가 참고한 실제 고객 발언 (RAG Source)
          </h4>
          <ul className="space-y-2">
            {insight.evidence_quotes && insight.evidence_quotes.length > 0 ? (
              insight.evidence_quotes.map((quote, idx) => (
                <li key={idx} className="text-xs text-slate-500 bg-white p-2 rounded border border-slate-200 italic">
                  "{quote}"
                </li>
              ))
            ) : (
              <li className="text-xs text-slate-400 bg-white p-2 rounded border border-slate-200">참고된 특정 리뷰 원문이 없습니다.</li>
            )}
          </ul>
        </div>
      )}

      {/* 피드백 입력 영역 (토글) */}
      {showFeedback && (
        <div className="p-5 border-t border-slate-100 bg-blue-50/30 animate-in zoom-in-95">
          <textarea
            placeholder="이 분석 내용에 대해 에이전트에게 지시할 사항을 적어주세요... (예: 이 부분은 긍정적인 톤으로 수정해줘)"
            className="w-full p-3 border border-blue-100 rounded-lg text-sm bg-white focus:ring-2 focus:ring-blue-400 outline-none resize-y min-h-[80px]"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
          <div className="flex justify-end gap-2 mt-3">
            <button 
              type="button"
              onClick={() => {
                setShowFeedback(false);
                setComment("");
              }}
              className="px-4 py-2 rounded-lg text-xs font-bold text-slate-500 hover:bg-slate-100 transition-colors"
            >
              취소
            </button>
            <button 
              type="button"
              onClick={handleSubmit} 
              disabled={isSubmitting || !comment.trim()}
              className="bg-blue-600 text-white px-5 py-2 rounded-lg text-xs font-bold shadow-md shadow-blue-200 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              피드백 전송
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default InsightCard;