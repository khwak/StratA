# StratA 경영 인사이트 리포트 ({{ detailed_metrics.period_info.target }})

## 1. 종합 요약
- **평균 KPI:** {{ summary.kpi }} / 5.0
- **경쟁사 대비 격차:** {{ summary.gap }}점 ({{ summary.level }})

## 2. 핵심 리스크 및 강점
### 주요 리스크
{% for risk in top_risks %}
- {{ risk.n }} (언급량: {{ risk.v }}건)
{% else %}
- 발견된 주요 리스크가 없습니다.
{% endfor %}

### 주요 강점
{% for strength in top_strengths %}
- {{ strength.n }} (언급량: {{ strength.v }}건)
{% else %}
- 발견된 주요 강점이 없습니다.
{% endfor %}

## 3. 맞춤형 경영 전략 (Action Plans)
### 단기 실행 계획
{% for plan in action_plans.shortTerm %}
#### {{ plan.title }}
{% for detail in plan.details %}
- {{ detail }}
{% endfor %}
  - *기대 효과:* {{ plan.expected_effect }}
{% else %}
- 수립된 단기 실행 계획이 없습니다.
{% endfor %}

### 장기 실행 계획
{% for plan in action_plans.longTerm %}
#### {{ plan.title }}
{% for detail in plan.details %}
- {{ detail }}
{% endfor %}
{% else %}
- 수립된 장기 실행 계획이 없습니다.
{% endfor %}

## 4. 전략 비평 (Critic Feedback)
> {{ critic_feedback }}