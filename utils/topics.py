import csv
from pathlib import Path

TOPICS_CSV = Path(__file__).parent.parent / "bible_verses_by_topic.csv"


def load_topics():
    topics = []
    with open(TOPICS_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            topic = row["Тема"].strip()
            verses = [v.strip() for v in row["Стихи"].split(";") if v.strip()]
            topics.append({"topic": topic, "verses": verses})
    return topics


def get_topics_list():
    return [t["topic"] for t in load_topics()]


def get_verses_for_topic(topic_name):
    for t in load_topics():
        if t["topic"] == topic_name:
            return t["verses"]
    return []
