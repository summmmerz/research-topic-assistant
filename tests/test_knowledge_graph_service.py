import json
import os
import unittest
import uuid

from app.modules.knowledge_graph.service import KnowledgeGraphService


class KnowledgeGraphServiceTest(unittest.TestCase):
    def setUp(self):
        temp_root = os.path.join(os.path.dirname(__file__), ".tmp")
        os.makedirs(temp_root, exist_ok=True)
        self.graph_path = os.path.join(temp_root, f"knowledge_graph_{uuid.uuid4().hex}.json")
        payload = {
            "nodes": [
                {"id": "paper_1", "label": "科研选题系统", "type": "论文", "keywords": ["大语言模型"]},
                {"id": "kw_1", "label": "大语言模型", "type": "关键词", "keywords": ["LLM"]},
                {"id": "kw_kg", "label": "知识图谱", "type": "关键词", "keywords": ["图结构"]},
                {"id": "kw_recommendation", "label": "推荐系统", "type": "关键词", "keywords": ["选题推荐"]},
                {"id": "author_1", "label": "测试作者", "type": "作者", "keywords": ["科研辅助"]},
            ],
            "edges": [
                {"source": "paper_1", "target": "kw_1", "relation": "研究主题"},
                {"source": "kw_kg", "target": "kw_recommendation", "relation": "增强"},
                {"source": "author_1", "target": "paper_1", "relation": "撰写"},
            ],
        }
        with open(self.graph_path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False)
        self.service = KnowledgeGraphService(graph_path=self.graph_path)

    def tearDown(self):
        if os.path.exists(self.graph_path):
            os.remove(self.graph_path)

    def test_status_contains_counts(self):
        status = self.service.get_status()
        self.assertEqual(status["total_nodes"], 5)
        self.assertEqual(status["total_edges"], 3)
        self.assertIn("论文", status["entity_types"])

    def test_search_and_entity_detail(self):
        results = self.service.search_entities(query="语言模型")
        self.assertGreaterEqual(len(results), 1)
        self.assertIn("kw_1", {item["id"] for item in results})

        entity = self.service.get_entity("paper_1")
        self.assertIsNotNone(entity)
        self.assertEqual(entity["label"], "科研选题系统")
        self.assertGreaterEqual(len(entity["related_nodes"]), 1)

    def test_search_matches_multiple_keywords_independently(self):
        results = self.service.search_entities(query="知识图谱 推荐系统")
        result_ids = {item["id"] for item in results}

        self.assertIn("kw_kg", result_ids)
        self.assertIn("kw_recommendation", result_ids)

    def test_visualization_filters_by_type(self):
        graph = self.service.get_visualization(entity_types=["关键词"], max_nodes=10)
        node_types = {node["type"] for node in graph["nodes"]}
        self.assertIn("关键词", node_types)
        self.assertLessEqual(len(graph["nodes"]), 5)


if __name__ == "__main__":
    unittest.main()
