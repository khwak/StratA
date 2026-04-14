import React, { useState } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Cell, ResponsiveContainer, ReferenceLine, LabelList, ReferenceArea } from 'recharts';

const IPAAnalysis = ({ ipaData }) => {
  const [selectedQuadrant, setSelectedQuadrant] = useState(null);

  const quadrants = [
    { id: 'Q1', title: 'Q1 유지영역', color: 'border-green-400', bg: 'rgba(74, 222, 128, 0.15)', desc: "고객이 중요하게 생각하며 만족도도 높은 영역입니다. 현재의 높은 수준을 지속적으로 유지하는 것이 핵심 경쟁력입니다." },
    { id: 'Q2', title: 'Q2 집중영역', color: 'border-red-400', bg: 'rgba(248, 113, 113, 0.15)', desc: "고객이 중요하게 생각하지만 만족도는 낮은 영역입니다. 자원을 집중하여 최우선으로 즉각적인 개선이 필요합니다." },
    { id: 'Q3', title: 'Q3 저순위영역', color: 'border-yellow-400', bg: 'rgba(250, 204, 21, 0.15)', desc: "중요도와 만족도가 모두 낮은 영역입니다. 현재로서는 추가적인 자원 투입의 우선순위가 상대적으로 낮습니다." },
    { id: 'Q4', title: 'Q4 과잉영역', color: 'border-blue-400', bg: 'rgba(59, 130, 246, 0.15)', desc: "만족도는 높으나 고객이 상대적으로 덜 중요하게 생각하는 영역입니다. 자원의 과잉 투자가 없는지 점검하고 재분배를 권장합니다." }
  ];

  const getQuadrant = (x, y) => {
    if (x >= 0 && y >= 0) return 'Q1';
    if (x < 0 && y >= 0) return 'Q2';
    if (x < 0 && y < 0) return 'Q3';
    if (x >= 0 && y < 0) return 'Q4';
    return null;
  };

  const enrichedData = ipaData?.map(d => ({
    ...d,
    quadrant: getQuadrant(d.x, d.y)
  })) || [];

  return (
    <div id="ipa" className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center scroll-mt-28">
      {/* 왼쪽: 항목 리스트 */}
      <div className="lg:col-span-4 space-y-4">
        {quadrants.map((q) => (
          <div 
            key={q.id} 
            onClick={() => setSelectedQuadrant(selectedQuadrant === q.id ? null : q.id)}
            className={`p-5 bg-white rounded-2xl shadow-sm border-l-8 cursor-pointer transition-all ${q.color} ${selectedQuadrant === q.id ? 'ring-2 ring-slate-200 shadow-md scale-102' : 'opacity-70'}`}
          >
            <h4 className="font-black text-slate-800 text-sm mb-1">{q.title}</h4>
            <p className="text-[12px] text-slate-500 leading-tight">{q.desc}</p>
          </div>
        ))}
      </div>

      {/* 오른쪽: 그래프 */}
      <div className="lg:col-span-8 bg-white p-10 rounded-[3rem] shadow-inner border border-slate-100 h-[500px] relative overflow-hidden">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 20, right: 40, bottom: 20, left: 20 }}>
            <XAxis type="number" dataKey="x" domain={[-2, 2]} hide />
            <YAxis type="number" dataKey="y" domain={[-2, 2]} hide />
            <ZAxis type="number" range={[150, 150]} />

            <ReferenceLine x={0} stroke="#cbd5e1" strokeWidth={2} />
            <ReferenceLine y={0} stroke="#cbd5e1" strokeWidth={2} />
            <Scatter data={enrichedData} isAnimationActive={false}>
              {enrichedData.map((entry, index) => {
                let dotColor = '#94a3b8';
                if (entry.quadrant === 'Q1') dotColor = '#4ade80';
                else if (entry.quadrant === 'Q2') dotColor = '#f87171'; 
                else if (entry.quadrant === 'Q3') dotColor = '#facc15'; 
                else if (entry.quadrant === 'Q4') dotColor = '#60a5fa'; 

                return (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={dotColor} 
                    opacity={!selectedQuadrant || entry.quadrant === selectedQuadrant ? 1 : 0.1} 
                    className="transition-opacity duration-300"
                  />
                );
              })}
              <LabelList dataKey="name" position="top" offset={10} style={{fontSize: '11px', fontWeight: '900', fill: '#64748b'}} />
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
        <div className="absolute top-4 left-1/2 -translate-x-1/2 text-[10px] font-black text-slate-400 uppercase">Importance</div>
        <div className="absolute right-4 top-1/2 -translate-y-1/2 text-[10px] font-black text-slate-400 uppercase rotate-90 origin-right">Performance</div>
      </div>
    </div>
  );
};
export default IPAAnalysis;