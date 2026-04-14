import React, { useEffect} from 'react';
import ExecutiveSummary from './ExecutiveSummary';
import IPAAnalysis from './IPAAnalysis';
import StrategicRoadmap from './StrategicRoadmap';
import MetricSummary from '../MetricSummary';

const VisualReportView = ({ data }) => {
  useEffect(() => {
    console.log("백엔드에서 받은 최종 리포트 데이터:", data?.final_report);
  }, [data]);

  const report = data?.final_report || {};

  // 1. 트렌드 데이터 가공 
  const trendData = (report.trend && report.trend.length > 0) ? report.trend : [
    { month: 'Jan', star: 4.0, pos: 70, neg: 30 },
    { month: 'Feb', star: 4.2, pos: 65, neg: 35 },
    { month: 'Mar', star: 3.8, pos: 75, neg: 25 },
    { month: 'Apr', star: 4.5, pos: 80, neg: 20 },
    { month: 'Mai', star: 4.1, pos: 70, neg: 30 },
    { month: 'Jun', star: 4.3, pos: 85, neg: 15 },
  ];

  // 2. 레이다 및 KPI 데이터 가공 
  const metrics = {
    trend: trendData,
    radar: report.radar && report.radar.length > 0 ? report.radar : [],
    summary: report.summary || { kpi: 0, gap: 0, level: "데이터 부족" },
    
    top_risks: report.top_risks || [],
    top_strengths: report.top_strengths || [],
    emerging_trends: report.emerging_trends || [],
    key_factors: report.key_factors || { strengths: [], risks: [] }
  };

  // 3. IPA 좌표 데이터 가공 
  const ipaData = report.ipa || [
    { name: '편안함', x: 1.2, y: 1.5, fill: '#f97316' },
    { name: '위치', x: 1.8, y: 0.9, fill: '#f97316' },
    { name: '청결도', x: -0.8, y: 1.3, fill: '#ef4444' },
    { name: '직원 친절도', x: -0.5, y: -0.2, fill: '#f59e0b' },
    { name: '가성비', x: -1.2, y: -0.8, fill: '#f59e0b' },
    { name: '시설', x: 1.1, y: -0.1, fill: '#3b82f6' },
  ];

  // 4. 전략 로드맵 데이터 가공 
  const plans = {
    shortTerm: report.action_plans?.shortTerm || [
      { 
        title: "1. 청결 리스크 긴급 안정화", 
        details: ["전 객실 방역 점검 실시", "청소 체크리스트 보완"] 
      },
      { 
        title: "2. 강점 영역 유지 및 활용", 
        details: ["편안함/위치 관련 긍정 리뷰 상단 노출"] 
      }
    ],
    longTerm: report.action_plans?.longTerm || [
      { 
        title: "1. 청결 체계 구조 개선", 
        details: ["SOP 전면 개편", "분기별 외부 위생 감사"] 
      }
    ]
  };
  
  // 5. 상세 지표 데이터
  const detailedMetrics = report.detailed_metrics;

  return (
    <div className="space-y-24 pb-40 animate-in fade-in slide-in-from-bottom-8 duration-1000">
      
      {/* 1 & 2. 핵심 트렌드 및 KPI 비교 */}
      <section id="trend" className="scroll-mt-28">
        <h2 className="text-3xl font-black text-slate-900 mb-10 uppercase tracking-tighter">
          Executive Summary
        </h2>
        <ExecutiveSummary metrics={metrics} trendData={trendData} />

        {detailedMetrics && (
          <div className="mt-12">
            <MetricSummary metrics={detailedMetrics} />
          </div>
        )}
      </section>

      {/* 3. IPA 분석 섹션 */}
      <section id="ipa" className="scroll-mt-28">
        <h2 className="text-3xl font-black text-slate-900 mb-10 uppercase tracking-tighter">
          속성별 인사이트 (IPA 분석)
        </h2>
        <IPAAnalysis ipaData={ipaData} />
      </section>

      {/* 4. 전략 로드맵 및 비평 섹션 */}
      <section id="strategy" className="scroll-mt-28">
        <h2 className="text-3xl font-black text-slate-900 mb-10 uppercase tracking-tighter">
          개선 포인트 - 단계별 전략 수립
        </h2>
        <StrategicRoadmap 
          plans={plans} 
          criticFeedback={report.critic_feedback || "총평 데이터를 분석 중입니다."} 
        />
      </section>

    </div>
  );
};

export default VisualReportView;