import os
import json
import unittest
import uuid

from app.modules.knowledge_graph.service import KnowledgeGraphService
from app.modules.topic_recommendation.database import TopicDatabase
from app.modules.topic_recommendation.multi_feature_algorithm import MultiFeatureRecommender


class TestMultiFeatureRecommender(unittest.TestCase):
    def setUp(self):
        temp_root = os.path.join(os.path.dirname(__file__), ".tmp")
        os.makedirs(temp_root, exist_ok=True)
        self.db_path = os.path.join(temp_root, f"topic_test_{uuid.uuid4().hex}.db")
        self.db = TopicDatabase(db_path=self.db_path)
        self.recommender = MultiFeatureRecommender(topic_db=self.db)
        self.graph_path = os.path.join(temp_root, f"topic_graph_{uuid.uuid4().hex}.json")

    def tearDown(self):
        if os.path.exists(self.graph_path):
            os.remove(self.graph_path)

    def test_weights_normalization(self):
        default_weights = self.recommender.get_weights()
        self.assertAlmostEqual(sum(default_weights.values()), 1.0)

        self.recommender.set_weights(
            {
                "semantic": 0.6,
                "hotness": 0.1,
                "centrality": 0.1,
                "mentor_match": 0.1,
            }
        )
        normalized = self.recommender.get_weights()
        self.assertAlmostEqual(sum(normalized.values()), 1.0)

    def test_semantic_similarity_range(self):
        topic = {
            "topic_key": "demo_topic",
            "title": "知识图谱增强推荐",
            "keywords": "知识图谱, 推荐系统, 科研选题",
        }
        score = self.recommender.calculate_semantic_similarity(topic, "我想研究知识图谱和选题推荐")
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_mentor_match(self):
        topic = {
            "topic_key": "demo_topic",
            "title": "知识图谱增强推荐",
            "keywords": "知识图谱, 推荐系统, 科研选题",
        }
        self.assertEqual(self.recommender.calculate_mentor_match(topic, None), 0.0)

        mentor = {
            "name": "知识图谱与推荐系统",
            "research": "知识图谱、推荐系统、可解释性",
            "keywords": "知识图谱 推荐系统",
        }
        score = self.recommender.calculate_mentor_match(topic, mentor)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_recommend_topics(self):
        results = self.recommender.recommend_topics(
            user_interest="大语言模型 科研助手 知识图谱",
            limit=3,
            domain="计算机科学",
        )
        self.assertGreater(len(results), 0)
        first = results[0]
        self.assertIn("topic_name", first)
        self.assertIn("reason_tags", first)
        self.assertIn("explanation", first)
        self.assertIn("summary", first["explanation"])
        self.assertLessEqual(len(results), 3)

    def test_feedback_score(self):
        topic_key = self.recommender.recommend_topics("知识图谱", limit=1)[0]["topic_key"]
        self.db.save_feedback("session-1", "rec-1", topic_key, "bookmark")
        score = self.recommender.calculate_feedback_score(topic_key)
        self.assertGreater(score, 0.5)

    def test_graph_candidates_are_merged_into_recommendations(self):
        graph = {
            "nodes": [
                {
                    "id": "direction_1",
                    "label": "知识图谱驱动的导师方向匹配",
                    "type": "研究方向",
                    "keywords": ["知识图谱", "导师匹配", "推荐系统"],
                },
                {"id": "kw_1", "label": "导师匹配", "type": "关键词", "keywords": ["导师匹配"]},
            ],
            "edges": [
                {"source": "direction_1", "target": "kw_1", "relation": "RELATED_TO"},
            ],
        }
        with open(self.graph_path, "w", encoding="utf-8") as file:
            json.dump(graph, file, ensure_ascii=False)

        kg_service = KnowledgeGraphService(graph_path=self.graph_path)
        recommender = MultiFeatureRecommender(topic_db=self.db, knowledge_graph_service=kg_service)
        results = recommender.recommend_topics("知识图谱 导师匹配", limit=5)
        self.assertTrue(any(item["topic_key"].startswith("kg_") for item in results))


if __name__ == "__main__":
    unittest.main()
