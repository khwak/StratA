import React from 'react';
import { Lightbulb } from 'lucide-react';

const StrategicRoadmap = ({ plans, criticFeedback }) => {
  const shortTermPlans = plans?.shortTerm || [];
  const longTermPlans = plans?.longTerm || [];

  return (
    <div id="strategy" className="space-y-12 scroll-mt-28">
      <div className="bg-slate-900 p-8 md:p-10 rounded-[2.5rem] text-white shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500 rounded-full blur-3xl opacity-10 pointer-events-none transform translate-x-1/2 -translate-y-1/2"></div>
        
        <div className="flex items-center gap-3 mb-6 text-blue-400 relative z-10">
          <Lightbulb size={28} />
          <h3 className="text-xl font-black uppercase tracking-tighter">종합 분석 총평</h3>
        </div>
        <div className="text-slate-300 text-base leading-relaxed font-medium relative z-10">
           {criticFeedback ? (
             criticFeedback.split('\n').map((line, idx) => (
               <p key={idx} className="mb-2">{line}</p>
             ))
           ) : (
             <p>종합 분석 결과를 불러오고 있습니다...</p>
           )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        
        {/* 단기 전략 (0-3개월) */}
        <div className="bg-white p-10 rounded-[2.5rem] shadow-xl border border-slate-50 relative overflow-hidden">
          <h3 className="text-xl font-black mb-10 text-slate-800 flex items-center gap-2">
            단기 전략 <span className="text-sm font-bold text-slate-400 tracking-tighter">(Quick Win)</span>
          </h3>
          <div className="space-y-10">
            {shortTermPlans.length === 0 ? (
              <p className="text-sm text-slate-400 font-medium">단기 전략 데이터를 분석 중입니다...</p>
            ) : (
              shortTermPlans.map((plan, index) => (
                <section key={`short-${index}`} className="space-y-3">
                  <h4 className="font-black text-slate-800 text-base">{plan.title}</h4>
                  <ul className="text-[14px] text-slate-500 list-disc ml-5 space-y-1 font-medium">
                    {plan.details.map((detail, dIdx) => (
                      <li key={dIdx}>{detail}</li>
                    ))}
                  </ul>
                  <p className="text-[12px] font-black text-indigo-500 mt-2 bg-indigo-50 inline-block px-2 py-1 rounded">
                    기대 효과: {plan.expected_effect}
                  </p>
                </section>
              ))
            )}
          </div>
        </div>

        {/* 장기 전략 (6-12개월) */}
        <div className="bg-white p-10 rounded-[2.5rem] shadow-xl border border-slate-50 relative overflow-hidden">
          <h3 className="text-xl font-black mb-10 text-slate-800 flex items-center gap-2">
            장기 전략 <span className="text-sm font-bold text-slate-400 tracking-tighter">(Long-term)</span>
          </h3>
          <div className="space-y-10">
            {longTermPlans.length === 0 ? (
              <p className="text-sm text-slate-400 font-medium">장기 전략 데이터를 분석 중입니다...</p>
            ) : (
              longTermPlans.map((plan, index) => (
                <section key={`long-${index}`} className="space-y-3">
                  <h4 className="font-black text-slate-800 text-base">{plan.title}</h4>
                  <ul className="text-[14px] text-slate-500 list-disc ml-5 space-y-1 font-medium">
                    {plan.details.map((detail, dIdx) => (
                      <li key={dIdx}>{detail}</li>
                    ))}
                  </ul>
                  <p className="text-[12px] font-black text-blue-600 mt-2 bg-blue-50 inline-block px-2 py-1 rounded">
                    기대 효과: {plan.expected_effect}
                  </p>
                </section>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StrategicRoadmap;