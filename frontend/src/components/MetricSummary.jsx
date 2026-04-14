import React from 'react';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

const MetricSummary = ({ metrics }) => {
  if (!metrics) return null;

  const { kpi_metrics = {}, growth_metrics = {}, competitive_gap = {} } = metrics;

  const renderTrend = (value) => {
    const safeValue = Number(value) || 0;
    if (safeValue > 0) return <span className="flex items-center text-blue-600"><ArrowUpRight size={14} /> {safeValue}</span>;
    if (safeValue < 0) return <span className="flex items-center text-red-600"><ArrowDownRight size={14} /> {Math.abs(safeValue)}</span>;
    return <span className="flex items-center text-slate-400"><Minus size={14} /> 0</span>;
  };

  const safeFormat = (val) => {
    const num = Number(val);
    return isNaN(num) ? "0.00" : num.toFixed(2);
  };

return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      <div className="p-6 border-b border-slate-100 bg-slate-50/50">
        <h2 className="text-xl font-bold text-slate-800">주요 KPI 분석</h2>
        <p className="text-xs text-slate-500 mt-1">대상 기간: {metrics.period_info?.target || "Unknown"}</p>
      </div>

      <div className="divide-y divide-slate-100">
        {Object.entries(kpi_metrics.scores || kpi_metrics).map(([key, value]) => {
          const compGap = competitive_gap[key] || 0;
          const momValue = growth_metrics?.mom?.[key] || 0;
          const yoyValue = growth_metrics?.yoy?.[key] || 0;

          return (
            <div key={key} className="p-6 hover:bg-slate-50 transition-colors">
              <div className="flex justify-between items-end mb-4">
                <div>
                  <span className="text-sm font-bold text-slate-400 uppercase tracking-wider">{key}</span>
                  <div className="text-3xl font-black text-slate-900 mt-1">
                    {safeFormat(value)}<small className="text-sm font-normal text-slate-400 ml-1">점</small>
                  </div>
                </div>
                {/* 경쟁사 대비 격차 (Competitive Gap) */}
                <div className="text-right">
                  <span className="text-[10px] font-bold text-slate-400 block mb-1">COMP. GAP</span>
                  <span className={`text-sm font-bold ${Number(compGap) >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                    {Number(compGap) > 0 ? '+' : ''}{compGap}
                  </span>
                </div>
              </div>

              {/* 시계열 변화율 (MoM, YoY) */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-50">
                <div>
                  <span className="text-[10px] font-bold text-slate-400 block mb-1 uppercase">MoM (전월비)</span>
                  <div className="text-sm font-bold">{renderTrend(momValue)}</div>
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-400 block mb-1 uppercase">YoY (전년비)</span>
                  <div className="text-sm font-bold">{renderTrend(yoyValue)}</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="p-4 bg-slate-50 border-t border-slate-100">
        <p className="text-[11px] text-slate-400 leading-tight">
          * 5.0 만점 기준이며, 하락 지표는 AI 에이전트가 원인 분석을 우선적으로 수행합니다.
        </p>
      </div>
    </div>
  );
};

export default MetricSummary;