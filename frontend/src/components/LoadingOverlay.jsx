import { useState, useEffect } from 'react';

const LoadingOverlay = ({ type = "init", customMessage = "" }) => {
  const defaultInitMsg = "에이전트 파이프라인 가동 중...";
  const displayMessage = customMessage || (type === "init" ? defaultInitMsg : "작업 진행 중...");

  return (
    <div className="fixed inset-0 bg-white/90 backdrop-blur-md z-50 flex flex-col items-center justify-center">
      <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-6"></div>
      
      <p className="text-xl font-bold text-slate-800 animate-pulse">
        {displayMessage}
      </p>
      
      <p className="text-sm text-slate-400 mt-2">
        {type === "init" 
          ? "데이터 수집 및 정량 지표 분석을 수행하고 있습니다." 
          : "에이전트가 실시간으로 전략을 검증하며 리포트를 작성하고 있습니다."}
      </p>
    </div>
  );
};

export default LoadingOverlay;