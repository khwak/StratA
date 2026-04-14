import React from 'react';
import { AreaChart, Area, BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis } from 'recharts';

const ExecutiveSummary = ({ metrics }) => {
  if (!metrics) {
    return <div className="p-8 text-center text-slate-500">데이터를 불러오는 중입니다...</div>;
  }

  const trendData = metrics.trend || [];
  const radarData = metrics.radar || [];
  const summary = metrics.summary || { kpi: 0, gap: 0, level: "데이터 없음" };
  
  const topRisks = metrics.top_risks || [
    { n: '청결도', v: 15, up: true }, 
    { n: '직원 말투', v: 5, up: true }, 
    { n: '예약 결제 플랫폼 용이', v: 3, up: false }
  ];
  
  const topStrengths = metrics.top_strengths || [
    { n: '조식 퀄리티', v: 12, up: true }, 
    { n: '침구 편안함', v: 8, up: true }, 
    { n: '접근성', v: 4, up: false }
  ];

  const radarStrengths = metrics.key_factors?.strengths || ['조식', '수영장 시설'];
  const radarRisks = metrics.key_factors?.risks || ['주차 공간 부족', '청결도'];

  const emergingTrends = metrics.emerging_trends || [
    { 
      title: "'호텔 호핑(Hotel Hopping)'의 확산", 
      desc: "한 여행지에서 한 곳에만 머물지 않고 여러 호텔을 옮겨 다니며 다양한 숙박 경험을 즐기는 여행자가 급증하고 있습니다." 
    },
    { 
      title: "'컴포트테크(Comfort-tech)'와 보이지 않는 AI", 
      desc: "화려한 기술보다는 고객의 수면 질을 높이거나 체크인을 간소화하는 등 실질적 편안함을 제공하는 기술이 표준이 되고 있습니다." 
    }
  ];

  return (
    <div className="space-y-16">
      {/* 섹션 1: 트렌드 및 키워드 (4개 카드) */}
      <div id="trend" className="grid grid-cols-1 md:grid-cols-2 gap-8 scroll-mt-28">
        
        {/* 카드 1: 리뷰 별점 변화 */}
        <div className="bg-white p-8 rounded-[2rem] shadow-xl border border-slate-50">
          <h3 className="font-bold text-slate-700 mb-6 text-lg">리뷰 별점 변화</h3>
          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="colorStar" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{fontSize: 10, fontWeight: 'bold', fill: '#94a3b8'}} />
                <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }} />
                <Area type="monotone" dataKey="star" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorStar)" isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 카드 2: 리스크 요인 Top 3 */}
        <div className="bg-white p-8 rounded-[2.5rem] shadow-xl border border-slate-50">
          <h3 className="font-bold text-slate-700 mb-6 text-lg">리스크 요인 키워드 Top 3</h3>
          <div className="space-y-5">
            {topRisks.map((item, i) => (
              <div key={i} className="flex justify-between items-center border-b border-slate-50 pb-2">
                <span className="font-bold text-slate-700">{i+1}. {item.n}</span>
                <span className={`font-black ${item.up ? 'text-red-500' : 'text-blue-500'}`}>{item.v} {item.up ? '▲' : '▼'}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 카드 3: 긍/부정 리뷰 비율 */}
        <div className="bg-white p-8 rounded-[2rem] shadow-xl border border-slate-50">
          <h3 className="font-bold text-slate-700 mb-6 text-lg">긍/부정 리뷰 비율 변화</h3>
          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trendData}>
                <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{fontSize: 10, fontWeight: 'bold', fill: '#94a3b8'}} />
                <Tooltip cursor={{fill: 'transparent'}} />
                <Bar dataKey="pos" fill="#3b82f6" stackId="a" radius={[0, 0, 0, 0]} barSize={24} />
                <Bar dataKey="neg" fill="#ef4444" stackId="a" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 카드 4: 차별화 요인 Top 3 */}
        <div className="bg-white p-8 rounded-[2.5rem] shadow-xl border border-slate-50">
          <h3 className="font-bold text-slate-700 mb-6 text-lg">차별화 요인 키워드 Top 3</h3>
          <div className="space-y-5">
            {topStrengths.map((item, i) => (
              <div key={i} className="flex justify-between items-center border-b border-slate-50 pb-2">
                <span className="font-bold text-slate-700">{i+1}. {item.n}</span>
                <span className={`font-black ${item.up ? 'text-red-500' : 'text-blue-500'}`}>{item.v} {item.up ? '▲' : '▼'}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 섹션 2: KPI & Radar */}
      <div id="kpi" className="scroll-mt-28">
        <div className="grid grid-cols-3 gap-6 mb-8">
          <div className="bg-indigo-50/50 p-6 rounded-2xl text-center border border-indigo-100/50">
            <p className="text-sm font-black text-indigo-400 uppercase tracking-widest mb-1">Hotel KPI</p>
            <p className="text-4xl font-black text-slate-900">{summary.kpi}</p>
          </div>
          <div className="bg-blue-50/50 p-6 rounded-2xl text-center border border-blue-100/50">
            <p className="text-sm font-black text-blue-400 uppercase tracking-widest mb-1">경쟁사 대비 격차</p>
            <p className={`text-3xl font-black ${summary.gap >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
              {summary.gap > 0 ? `+${summary.gap}` : summary.gap}
            </p>
          </div>
          <div className="bg-slate-100/50 p-6 rounded-2xl text-center border border-slate-200/50 flex flex-col justify-center">
            <p className="text-sm font-black text-slate-400 uppercase tracking-widest mb-1">경쟁 우위 레벨</p>
            <p className="text-2xl font-black text-slate-700 tracking-tighter">{summary.level}</p>
          </div>
        </div>

        <div className="bg-white p-10 rounded-[2.5rem] shadow-xl border border-slate-50 grid grid-cols-1 lg:grid-cols-5 gap-10">
          
          {/* 레이다 차트 영역 */}
          <div className="lg:col-span-2 flex flex-col items-center justify-center border-r border-slate-50">
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#f1f5f9" />
                  <PolarAngleAxis dataKey="subject" tick={{fontSize: 12, fontWeight: 'black', fill: '#64748b'}} />
                  <Radar name="자사" dataKey="A" stroke="#818cf8" fill="#818cf8" fillOpacity={0.5} />
                  <Radar name="경쟁사" dataKey="B" stroke="#c7d2fe" fill="#c7d2fe" fillOpacity={0.3} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            <div className="flex gap-4 mt-2">
              <div className="flex items-center gap-2"><div className="w-3 h-3 bg-[#818cf8] rounded-sm"></div><span className="text-[12px] font-bold text-slate-400">자사</span></div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 bg-[#c7d2fe] rounded-sm"></div><span className="text-[12px] font-bold text-slate-400">경쟁사</span></div>
            </div>
          </div>

          {/* 강점/리스크 및 트렌드 텍스트 영역 */}
          <div className="lg:col-span-3 space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50/50 p-4 rounded-xl border border-blue-100/50 text-center">
                <p className="text-base font-bold text-blue-600 mb-1 tracking-tight">주요 강점</p>
                <p className="text-sm font-black text-slate-800 leading-tight">
                  {radarStrengths.map((str, idx) => <React.Fragment key={idx}>{str}<br/></React.Fragment>)}
                </p>
              </div>
              <div className="bg-red-50/50 p-4 rounded-xl border border-red-100/50 text-center">
                <p className="text-base font-bold text-red-600 mb-1 tracking-tight">주요 리스크</p>
                <p className="text-sm font-black text-slate-800 leading-tight">
                  {radarRisks.map((risk, idx) => <React.Fragment key={idx}>{risk}<br/></React.Fragment>)}
                </p>
              </div>
            </div>
            
            <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100">
              <p className="font-black text-slate-800 mb-3 text-base flex items-center gap-2 underline decoration-indigo-300 underline-offset-4">주요 트렌드 인사이트</p>
              <div className="text-[14px] text-slate-600 space-y-3 leading-relaxed">
                {emergingTrends.map((trend, idx) => (
                  <p key={idx}>
                    <strong className="text-slate-900">{idx + 1}. {trend.title}</strong> <br/>
                    {trend.desc}
                  </p>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExecutiveSummary;