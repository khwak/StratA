import re 
from collections import Counter
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

class DeepDiscoveryEngine:
    def __init__(self):
        print("[Discovery Engine] Loading Embedding Model...")
        self.embedding_model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")

        self.hf_repo_id = "khwak/strata-bertopic"

        print(f"[Discovery Engine] Loading BERTopic from Hugging Face Hub ({self.hf_repo_id})...")
        try:
            self.topic_model = BERTopic.load(self.hf_repo_id, embedding_model=self.embedding_model)
            print("[Discovery Engine] BERTopic loaded successfully!")
        except Exception as e:
            print(f"[Discovery Engine] Failed to load from HF Hub. Error: {e}")
            print("[Discovery Engine] 로컬 경로(fallback)로 로드를 시도할 수 있도록 코드를 수정해주세요.")

    def _extract_topics(self, reviews: list) -> list: 
        if not reviews: 
            return []
        
        all_sentences = []
        for review in reviews:
            content = review.get("text", "")
            sentences = re.split(r'[.?!,\n]+', content)
            all_sentences.extend([s.strip() for s in sentences if s.strip()])
            
        if not all_sentences: 
            return []
        
        topics, probs = self.topic_model.transform(all_sentences)

        valid_topics = [t for t in topics if t != -1]
        topic_counts = Counter(valid_topics)

        results = []
        for topic_id, count in topic_counts.most_common(10): 
            topic_info = self.topic_model.get_topic_info(topic_id)
            if not topic_info.empty:
                topic_name = topic_info.iloc[0]["Name"]
                keywords = [word for word, _ in self.topic_model.get_topic(topic_id)[:3]]
                
                results.append({
                    "topic": topic_name,
                    "count": count,
                    "keywords": keywords
                })
        return results
    
    def discover_risks(self, reviews: list) -> list:
        negative_reviews = [r for r in reviews if r.get("rating", 0) > 0 and r.get("rating", 5) <= 2]
        target_reviews = negative_reviews if negative_reviews else reviews
        
        topics = self._extract_topics(target_reviews)
        for t in topics: 
            t["severity"] = "High" if t["count"] > 5 else "Medium"
        return topics
    
    def discover_strengths(self, reviews: list) -> list:
        positive_reviews = [r for r in reviews if r.get("rating", 3) >= 4]
        target_reviews = positive_reviews if positive_reviews else reviews
        
        topics = self._extract_topics(target_reviews)
        for t in topics: 
            t["sentiment"] = "Positive"
        return topics
    
    def discover_trends(self, reviews: list) -> list:
        topics = self._extract_topics(reviews)
        return topics[:3]

    def compare_unique_factors(self, my_list: list, comp_list: list) -> list:
        comp_topics = {item.get('topic') for item in comp_list if isinstance(item, dict) and item.get('topic')}
        unique_items = []
        for item in my_list:
            if isinstance(item, dict) and item.get('topic') not in comp_topics:
                unique_items.append(item)
        return unique_items

discovery_engine = DeepDiscoveryEngine()