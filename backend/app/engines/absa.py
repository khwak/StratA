import os
import re
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class DeepABSAEngine:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[ABSA Engine] Using device: {self.device}")

        mpnet_repo_id = "khwak/strata-mpnet"
        xlm_r_repo_id = "khwak/strata-xlm-r"

        hf_token = os.environ.get("HF_TOKEN")

        # MPNet - Category classifier 로드
        print(f"[ABSA Engine] Loading MPNet from Hugging Face ({mpnet_repo_id})...")
        self.mpnet_tokenizer = AutoTokenizer.from_pretrained(mpnet_repo_id, token=hf_token)
        self.mpnet_model = AutoModelForSequenceClassification.from_pretrained(mpnet_repo_id, token=hf_token)
        self.mpnet_model.to(self.device)
        self.mpnet_model.eval()

        # XLM-RoBERTa - Sentiment Classifier 로드
        print(f"[ABSA Engine] Loading XLM-RoBERTa from Hugging Face ({xlm_r_repo_id})...")
        self.xlm_tokenizer = AutoTokenizer.from_pretrained(xlm_r_repo_id, token=hf_token)
        self.xlm_model = AutoModelForSequenceClassification.from_pretrained(xlm_r_repo_id, token=hf_token)
        self.xlm_model.to(self.device)
        self.xlm_model.eval()

        self.mpnet_id2label = self.mpnet_model.config.id2label

        # 설정값
        self.batch_size = 32
        self.threshold = 0.45

        self.category_to_kpi = {
            "cleanliness": "청결",
            "service": "서비스",
            "facilities": "시설",
            "price": "가격"
        }
        self.kpi_keys = ["청결", "서비스", "시설", "가격"]

    def _batch_process(self, data: list) -> list:
        return [data[i:i + self.batch_size] for i in range(0, len(data), self.batch_size)]
    
    def _predict_categories_batch(self, sentences: list) -> list:
        results = []
        batches =  self._batch_process(sentences)

        with torch.no_grad():
            for batch in batches:
                inputs = self.mpnet_tokenizer(batch, padding=True, truncation=True, max_length=128, return_tensors="pt").to(self.device)
                outputs = self.mpnet_model(**inputs)

                probs = torch.sigmoid(outputs.logits)

                for prob_array in probs:
                    active_indices = torch.where(prob_array > self.threshold)[0].tolist()
                    
                    active_categories = []
                    for idx in active_indices:
                        key = str(idx) if str(idx) in self.mpnet_id2label else idx
                        cat_name = self.mpnet_id2label.get(key, "Unknown")
                        active_categories.append(cat_name)
                        
                    results.append(active_categories)
        
        return results

    def _predict_sentiment_batch(self, prompt_pairs: list) -> list:
        results = []
        batches = self._batch_process(prompt_pairs)

        with torch.no_grad():
            for batch in batches:
                inputs = self.xlm_tokenizer(batch, padding=True, truncation=True, max_length=128, return_tensors="pt").to(self.device)
                outputs = self.xlm_model(**inputs)

                probs = torch.softmax(outputs.logits, dim=1)

                id2label_xlm = self.xlm_model.config.id2label
                pos_idx, neg_idx = 1, 0
                for idx, label in id2label_xlm.items():
                    if label.lower() == "positive": pos_idx = int(idx)
                    elif label.lower() == "negative": neg_idx = int(idx)

                for prob in probs:
                    score = prob[pos_idx].item() - prob[neg_idx].item()
                    results.append(score)

        return results
 
    def calculate_metrics(self, reviews: list) -> dict:
        print(f"\n[ABSA DEBUG] 입력된 리뷰 데이터 개수: {len(reviews)}건")

        if not reviews:
            print("  -> [Return] 리뷰 데이터가 없어 기본값(2.5)을 반환.")
            return {"scores": {kpi: 2.5 for kpi in self.kpi_keys}, "frequencies": {kpi: 0 for kpi in self.kpi_keys}}

        all_sentences_ko = []
        all_sentences_en = []

        for review in reviews:
            ko_text = review.get("text", "")
            en_text = review.get("text_en", ko_text)

            ko_sentences = [s.strip() for s in re.split(r'[.?!,\n]+', ko_text) if s.strip()]
            en_sentences = [s.strip() for s in re.split(r'[.?!,\n]+', en_text) if s.strip()]

            min_len = min(len(ko_sentences), len(en_sentences))
            all_sentences_ko.extend(ko_sentences[:min_len])
            all_sentences_en.extend(en_sentences[:min_len])
        
        print(f"[ABSA DEBUG] 분리된 문장 개수: 한국어 {len(all_sentences_ko)}개 / 영어 {len(all_sentences_en)}개")

        if not all_sentences_ko:
            print("  -> [Return] 추출된 문장이 없어 기본값(2.5)을 반환.")
            return {"scores": {kpi: 2.5 for kpi in self.kpi_keys}, "frequencies": {kpi: 0 for kpi in self.kpi_keys}}
                
        print("[ABSA DEBUG] MPNet 카테고리 예측 시작...")
        sentence_categories = self._predict_categories_batch(all_sentences_en)
        print(f"  -> 첫 3개 문장 예측 결과: {sentence_categories[:3]}")

        prompts = []
        meta_info = []

        unique_detected = set([cat for sublist in sentence_categories for cat in sublist])
        print(f"[ABSA DEBUG] 모델이 찾아낸 고유 카테고리 개수: {len(unique_detected)}개")
        if unique_detected:
            print(f"[ABSA Debug] 모델 탐지 카테고리 샘플: {list(unique_detected)[:5]}")
        else:
            print("  -> 주의: 모델이 단 하나의 카테고리도 확신하지 못했습니다. (Threshold 확인 요망)")

        mapping_success_count = 0
        mapping_fail_samples = set()

        for sentence_ko, categories in zip(all_sentences_ko, sentence_categories):
            for category in categories:
                normalized_cat = category.lower().replace("_", " ").strip()
                kpi = self.category_to_kpi.get(normalized_cat)

                if kpi:
                    mapping_success_count += 1
                    prompt_text = f"Sentence: {sentence_ko} Aspect: {category} Category: {category}"
                    prompts.append(prompt_text)
                    meta_info.append(kpi)
                else:
                    mapping_fail_samples.add(category)

        print(f"[ABSA DEBUG] KPI 매핑 결과: 성공 {mapping_success_count}건")
        if mapping_fail_samples:
            print(f"  -> 매핑 실패 카테고리 샘플: {list(mapping_fail_samples)[:5]}")

        agg_scores = {kpi: [] for kpi in self.kpi_keys}
        category_detail_scores = {}

        if prompts:
            sentiment_scores = self._predict_sentiment_batch(prompts)
            print(f"\n[ABSA Debug] 전체 영어 문장 개수: {len(all_sentences_en)}개")
            extracted_categories = set([cat for sublist in sentence_categories for cat in sublist])

            if not extracted_categories:
                print("[ABSA Debug] 오류: 모델이 카테고리를 단 한 개도 찾지 못했습니다! (Threshold를 더 낮추거나 문장 번역 확인 필요)")
                if all_sentences_en:
                    print(f"[ABSA Debug] 첫 번째 영어 문장 샘플: {all_sentences_en[0]}")
            else:
                print(f"[ABSA Debug] 모델이 찾은 고유 카테고리 목록: {extracted_categories}")

            for prompt, kpi, score, category in zip(prompts, meta_info, sentiment_scores, [p.split("Category: ")[1] for p in prompts]):

                if kpi:
                    agg_scores[kpi].append(score)

                if category not in category_detail_scores:
                    category_detail_scores[category] = []
                category_detail_scores[category].append(score)

            print("\n--- [ABSA] 카테고리별 평균 점수 ---")
            for cat, scores in category_detail_scores.items():
                cat_avg = np.mean(scores)
                print(f"  [Category Avg] {cat:30} : {cat_avg:6.2f} (데이터 {len(scores)}건)")
        else:
            print("[ABSA DEBUG] 감성 분석을 수행할 프롬프트가 없습니다.")

        # 최종 집계
        final_scores = {}
        frequencies = {}
        for kpi in self.kpi_keys:
            scores = agg_scores[kpi]
            frequencies[kpi] = len(scores)  
            
            if scores:
                avg = np.mean(scores)  
                val_5_scale = float(round((avg + 1) * 2.5, 2))
                final_scores[kpi] = float(round((avg + 1) * 2.5, 2)) 
                print(f"  [KPI Result] {kpi:4} : {val_5_scale:5.2f} / 5.0 (Raw Avg: {avg:6.2f} | 언급 빈도: {len(scores)})")
            else:
                final_scores[kpi] = 2.5
                print(f"  [KPI Result] {kpi:4} : 2.50 (데이터 없음)")
        
        return {
            "scores": final_scores,
            "frequencies": frequencies
        }

    def calculate_gap(self, base_metrics: dict, target_metrics: dict) -> dict:
        gap = {}
        base_scores = base_metrics.get("scores", base_metrics) if isinstance(base_metrics, dict) else base_metrics
        target_scores = target_metrics.get("scores", target_metrics) if isinstance(target_metrics, dict) else target_metrics

        for kpi in self.kpi_keys:
            val_base = base_scores.get(kpi, 2.5)
            val_target = target_scores.get(kpi, 2.5)
            gap[kpi] = float(round(val_base - val_target, 2))
        return gap
    
    def calculate_ipa(self, metrics: dict) -> list:
        scores = metrics.get("scores", {})
        freqs = metrics.get("frequencies", {})

        avg_score = np.mean(list(scores.values())) if scores else 2.5
        avg_freq = np.mean(list(freqs.values())) if freqs else 0

        ipa_data = []
        for kpi in self.kpi_keys:
            score = scores.get(kpi, 2.5)
            freq = freqs.get(kpi, 0)

            x = float(round(score - avg_score, 2))
            y = float(round(freq - avg_freq, 2))

            if x < 0 and y >= 0:
                fill, quadrant = "#ef4444", "Q2"  
            elif x >= 0 and y >= 0:
                fill, quadrant = "#22c55e", "Q1"  
            elif x < 0 and y < 0:
                fill, quadrant = "#f59e0b", "Q3"  
            else:
                fill, quadrant = "#3b82f6", "Q4" 

            ipa_data.append({
                "name": kpi,
                "x": x,
                "y": y,
                "fill": fill,
                "quadrant": quadrant
            })
        return ipa_data

    def calculate_radar(self, my_metrics: dict, comp_metrics: dict) -> list:
        my_scores = my_metrics.get("scores", {})
        comp_scores = comp_metrics.get("scores", {})

        radar_data = []
        for kpi in self.kpi_keys:
            my_val = float(round((my_scores.get(kpi, 2.5) / 5.0) * 100, 1))
            comp_val = float(round((comp_scores.get(kpi, 2.5) / 5.0) * 100, 1))

            radar_data.append({
                "subject": kpi,
                "A": my_val,     
                "B": comp_val    
            })
        return radar_data

absa_engine = DeepABSAEngine()