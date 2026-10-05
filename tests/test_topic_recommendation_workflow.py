import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone

from app.modules.topic_recommendation.database import TopicDatabase
from app.modules.topic_recommendation.multi_feature_algorithm import MultiFeatureRecommender
from app.modules.topic_recommendation.stage_based import StageBasedRecommender


class TopicRecommendationWorkflowTest(unittest.TestCase):
    def setUp(self):
        temp_root = os.path.join(os.path.dirname(__file__), ".tmp")
        os.makedirs(temp_root, exist_ok=True)
        self.db_path = os.path.join(temp_root, f"topic_test_{uuid.uuid4().hex}.db")
        self.db = TopicDatabase(db_path=self.db_path)
        self.recommender = MultiFeatureRecommender(topic_db=self.db)
        self.workflow = StageBasedRecommender(topic_db=self.db)

    def tearDown(self):
        pass

    def test_recommendation_contains_explanation_and_feedback_score(self):
        results = self.recommender.recommend_topics(
            user_interest="计算机科学 人工智能 大语言模型 科研辅助",
            limit=3,
            domain="计算机科学",
        )

        self.assertGreater(len(results), 0)
        first = results[0]
        self.assertIn("explanation", first)
        self.assertIn("reason_tags", first)
        self.assertIn("feedback_score", first)
        self.assertIn("summary", first["explanation"])

    def test_feedback_changes_summary_counts(self):
        session_id = self.workflow.create_session()
        results = self.recommender.recommend_topics("知识图谱 推荐系统", limit=1)
        topic_key = results[0]["topic_key"]

        response = self.workflow.submit_feedback(
            session_id=session_id,
            recommendation_id="rec-1",
            topic_key=topic_key,
            feedback_type="bookmark",
        )

        self.assertTrue(response["success"])
        summary = self.db.get_feedback_summary(topic_key)
        self.assertEqual(summary["bookmark"], 1)

    def test_import_topics_from_file(self):
        seed_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "data", "topics_seed.json")
        )

        result = self.workflow.import_topics_from_file(seed_path, source="test_import")
        self.assertTrue(result["success"])
        self.assertGreaterEqual(result["imported"], 1)

        topics = self.db.search_topics(domain="金融学", limit=10)
        self.assertTrue(any(topic["topic_key"] == "financial_llm_risk_control" for topic in topics))

    def test_stage_flow_generates_recommendations(self):
        session_id = self.workflow.create_session()
        self.workflow.submit_stage(session_id, 1, {"selection": "计算机科学"})
        self.workflow.submit_stage(session_id, 2, {"selection": "知识工程"})
        self.workflow.submit_stage(session_id, 3, {"selection": "知识图谱"})
        self.workflow.submit_stage(session_id, 4, {"input": "熟悉 Python 和 Flask"})
        result = self.workflow.submit_stage(
            session_id,
            5,
            {"input": "导师关注知识图谱和推荐系统"},
        )

        self.assertTrue(result["success"])
        self.assertGreater(len(result["recommendations"]), 0)

    def test_go_back_rebuilds_user_info_and_clears_recommendations(self):
        session_id = self.workflow.create_session()
        self.workflow.submit_stage(session_id, 1, {"selection": "计算机科学"})
        self.workflow.submit_stage(session_id, 2, {"selection": "知识工程"})
        self.workflow.submit_stage(session_id, 3, {"selection": "知识图谱"})
        self.workflow.sessions[session_id]["recommendations"] = [{"id": "demo"}]

        result = self.workflow.go_back(session_id)

        self.assertTrue(result["success"])
        session = self.workflow.sessions[session_id]
        self.assertEqual(session["stage"], 3)
        self.assertEqual(session["user_info"]["domain"], "计算机科学")
        self.assertEqual(session["user_info"]["base_direction"], "知识工程")
        self.assertNotIn("sub_direction", session["user_info"])
        self.assertEqual(session["recommendations"], [])

    def test_cleanup_expired_sessions_removes_inactive_session(self):
        active_session = self.workflow.create_session()
        expired_session = self.workflow.create_session()
        self.workflow.sessions[expired_session]["last_activity"] = (
            datetime.now(timezone.utc) - timedelta(hours=48)
        ).isoformat()

        removed = self.workflow.cleanup_expired_sessions(max_age_hours=24)

        self.assertEqual(removed, 1)
        self.assertIn(active_session, self.workflow.sessions)
        self.assertNotIn(expired_session, self.workflow.sessions)


if __name__ == "__main__":
    unittest.main()
