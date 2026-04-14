import React from 'react';

const ReportNavigation = () => {
  const menus = [
    { id: 'trend', name: '핵심 트렌드' },
    { id: 'kpi', name: 'KPI 분석' },
    { id: 'ipa', name: '속성별 분석' },
    { id: 'strategy', name: '전략 로드맵' }
  ];

  const scroll = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <nav className="fixed right-8 top-1/2 -translate-y-1/2 z-50 hidden xl:flex flex-col gap-4 items-end">
      {menus.map((menu) => (
        <button
          key={menu.id}
          onClick={() => scroll(menu.id)}
          className="group flex items-center gap-3 text-right cursor-pointer"
        >
          <span className="opacity-0 group-hover:opacity-100 transition-all duration-200 text-[12px] font-black text-slate-500 bg-white px-2 py-1 rounded shadow-sm border border-slate-100 whitespace-nowrap">
            {menu.name}
          </span>
          <div className="w-3 h-3 rounded-full bg-slate-300 group-hover:bg-blue-600 group-hover:scale-125 transition-all shadow-sm border border-white shrink-0"></div>
        </button>
      ))}
    </nav>
  );
};

export default ReportNavigation;