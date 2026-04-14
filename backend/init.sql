CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS strategy_history (
    id SERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    success_rate FLOAT DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    pref_style TEXT NOT NULL
);

INSERT INTO user_preferences (pref_style) 
VALUES ('일반적인 경영 전략 및 데이터 기반의 객관적 접근 선호');