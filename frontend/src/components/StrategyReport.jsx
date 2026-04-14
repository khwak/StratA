import React from 'react';
import { CheckCircle2, AlertTriangle, TrendingUp, ShieldCheck } from 'lucide-react';

const StrategyReport = ({ report }) => {
  if (!report || !report.action_plans) return null;

  return (
    <div className="mt-12 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="text-center">
        <h2 className="text-3xl font-black text-slate-900 flex items-center justify-center gap-3">
          <ShieldCheck className="text-blue-600" size={32} />
          최종 경영 전략 보고서
        </h2>
        <p className="text-slate-500 mt-2">에이전트 협업을 통해 도출된 최적의 액션 플랜입니다.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {report.action_plans.map((plan, idx) => (
          <div key={idx} className="bg-white p-6 rounded-2xl border-2 border-blue-50 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
                {idx + 1}
              </div>
              <h3 className="font-bold text-lg text-slate-800">{plan.title}</h3>
            </div>
            
            <p className="text-slate-600 text-sm mb-4 leading-relaxed">{plan.description}</p>
            
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
              <h4 className="text-[10px] font-black text-slate-400 uppercase mb-2">예상 기대 효과</h4>
              <p className="text-blue-700 font-bold text-sm flex items-center gap-1">
                <TrendingUp size={14} /> {plan.expected_impact}
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-amber-50 border-2 border-amber-100 p-8 rounded-3xl">
        <div className="flex items-center gap-2 mb-4 text-amber-700">
          <AlertTriangle size={24} />
          <h3 className="font-black text-xl">전문가 제언 (Critic Review)</h3>
        </div>
        <p className="text-amber-900 text-sm leading-relaxed italic">
          "{report.critic_feedback}"
        </p>
      </div>
    </div>
  );
};

export default StrategyReport;