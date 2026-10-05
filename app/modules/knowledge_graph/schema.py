# -*- coding: utf-8 -*-
"""Knowledge graph labels, relationship names and index definitions."""

NODE_LABELS = [
    "Paper",
    "Author",
    "Institution",
    "Keyword",
    "ResearchDirection",
    "FundProject",
    "Venue",
]

RELATIONSHIP_TYPES = [
    "WROTE",
    "AFFILIATED_WITH",
    "HAS_KEYWORD",
    "CITES",
    "COOPERATES_WITH",
    "BELONGS_TO",
    "FUNDED_BY",
]

INDEX_DEFINITIONS = [
    ("Paper", "id"),
    ("Paper", "title"),
    ("Author", "name"),
    ("Keyword", "name"),
    ("ResearchDirection", "name"),
]

TYPE_TO_LABEL = {
    "论文": "Paper",
    "作者": "Author",
    "机构": "Institution",
    "关键词": "Keyword",
    "研究方向": "ResearchDirection",
    "基金项目": "FundProject",
    "期刊": "Venue",
    "会议": "Venue",
}
