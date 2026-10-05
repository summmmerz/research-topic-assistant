import unittest

from app.modules.knowledge_graph.ingestion.entity_resolution import EntityResolver
from app.modules.knowledge_graph.ingestion.extractor import MetadataExtractor
from app.modules.knowledge_graph.ingestion.normalizer import MetadataNormalizer
from app.modules.knowledge_graph.ingestion.relation_builder import RelationBuilder


class KnowledgeGraphIngestionTest(unittest.TestCase):
    def test_pipeline_builds_academic_graph(self):
        records = [
            {
                "论文题名": "知识图谱增强的科研选题推荐方法",
                "作者": "教师B; 学生A",
                "机构": "UIBE",
                "关键词": "知识图谱; 推荐系统",
                "摘要": "系统使用 Neo4j 和大语言模型实现科研选题推荐。",
                "年份": "2025",
                "期刊": "智能教育研究",
            }
        ]

        normalized = MetadataNormalizer().normalize(records)
        extracted = MetadataExtractor().extract(normalized)
        resolved = EntityResolver().resolve(extracted)
        graph = RelationBuilder().build(resolved)

        labels = {node["label"] for node in graph["nodes"]}
        relations = {edge["relation"] for edge in graph["edges"]}
        self.assertIn("知识图谱增强的科研选题推荐方法", labels)
        self.assertIn("对外经济贸易大学", labels)
        self.assertIn("WROTE", relations)
        self.assertIn("HAS_KEYWORD", relations)
        self.assertIn("AFFILIATED_WITH", relations)


if __name__ == "__main__":
    unittest.main()
