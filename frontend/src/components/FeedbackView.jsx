import InsightCard from './InsightCard';
import MetricSummary from './MetricSummary';

const FeedbackView = ({ data, onUpdate, onConfirm }) => {
    return (        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 왼쪽 컬럼: 인사이트 영역 */}
          <section className="lg:col-span-2 space-y-6">
            <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
              핵심 분석 인사이트 
              <span className="text-xs font-normal text-slate-400">(상세 내용을 클릭하여 수정 지시 가능)</span>
            </h2>
            {!data ? (
              <div className="h-64 border-2 border-dashed rounded-2xl flex items-center justify-center text-slate-300 font-medium">
                상단 버튼을 눌러 분석을 시작하세요.
              </div>
            ) : (
              data.insights.map(item => (
                <InsightCard key={item.id} insight={item} threadId={data.thread_id} onUpdate={onUpdate} />
              ))
            )}

            {/* 최종 승인 버튼: 보고서 데이터가 아직 없을 때만 표시 */}
            {data && (!data.final_report || !data.final_report.action_plans) && (
              <div className="mt-8 flex justify-center border-t pt-8">
                <button 
                  onClick={onConfirm}
                  className="
                    bg-blue-600 text-white px-10 py-4 rounded-xl font-black text-lg 
                    shadow-xl shadow-blue-100 hover:bg-blue-700 
                    transition-all transform hover:-translate-y-1 active:scale-95
                  "
                >
                  분석 확정 및 경영 전략 수립 시작
                </button>
              </div>
            )}
          </section>

          {/* 오른쪽 컬럼: KPI 지표 영역 */}
          <section className="space-y-6">
            <h2 className="text-xl font-bold text-slate-800">주요 KPI 지표</h2>
            {!data ? (
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 py-10 text-center text-slate-300 text-sm">
                데이터가 없습니다.
              </div>
            ) : (
              <MetricSummary metrics={data.metrics} />
            )}
          </section>
        </div>
    );
};

export default FeedbackView;
