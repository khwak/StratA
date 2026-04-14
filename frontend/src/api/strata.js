import axios from 'axios';

// 백엔드 서버 주소
const API_BASE_URL = "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const strataApi = {
  // 1. 분석 시작
  initStream: async (period, mode, file, onProgress) => {
    const formData = new FormData();
    formData.append("target_period", period);
    formData.append("analysis_mode", mode);
    
    if (file) {
      formData.append("file", file);
    }

    const response = await fetch(`${API_BASE_URL}/init`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) throw new Error("Init stream connection failed");

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let done = false;
    let buffer = "";

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      if (value) {
        buffer += decoder.decode(value, { stream: true });
        let lines = buffer.split('\n');
        buffer = lines.pop();
        
        for (const line of lines) {
          if (line.trim() === '') continue;
          try {
            const parsedData = JSON.parse(line);
            
            if (parsedData.type === 'error') {
              console.error("Backend Stream Error:", parsedData.message);
              onProgress({ type: 'error', message: parsedData.message });
              done = true; 
              break;
            }
            
            onProgress(parsedData); 
          } catch (e) {
            console.error("Chunk JSON parse error", line, e);
          }
        }
      }
    }
  },
  
  // 2. 피드백 전송
  sendFeedback: (threadId, targetId, comment) => 
    api.post('/feedback', { thread_id: threadId, target_id: targetId, comment: comment }),
  
  // 3. 최종 승인
  confirmStream: async (threadId, onProgress) => {
    const response = await fetch(`${API_BASE_URL}/confirm`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ thread_id: threadId }),
    });

    if (!response.ok) throw new Error("Stream connection failed");

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let done = false;
    let buffer = "";

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      if (value) {
        buffer += decoder.decode(value, { stream: true });
        let lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (line.trim() === '') continue;

          try {
            const parsedData = JSON.parse(line);

            if (parsedData.type === 'error') {
              console.error("Backend Stream Error:", parsedData.message);
              onProgress(parsedData); 
              done = true; 
              break;      
            }

            onProgress(parsedData); 
          } catch (e) {
            console.error("Chunk JSON parse error", line, e);
          }
        }
      }
    }
  },
};