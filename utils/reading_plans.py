# coding: utf-8
"""
Модуль для хранения и парсинга планов чтения Библии из текстовых файлов.
"""
import re
from pathlib import Path
from typing import List, Dict, Tuple

class ReadingPlan:
    def __init__(self, plan_id: str, title: str, days: List[Dict]):
        self.plan_id = plan_id
        self.title = title
        self.days = days  # [{'day': 1, 'text': '...', 'entries': [...]}, ...]

    @staticmethod
    def parse_txt_plan(filepath: str, plan_id: str, title: str = None) -> 'ReadingPlan':
        """
        Парсит txt-файл с планом чтения. Возвращает ReadingPlan.
        """
        days = []
        current_day = None
        entries = []
        with open(filepath, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                m = re.match(r'[□\-\s]*День (\d+)\s*[—-]\s*(.+)', line)
                if m:
                    if current_day:
                        days.append({'day': current_day, 'text': day_text, 'entries': entries})
                    current_day = int(m.group(1))
                    day_text = m.group(2)
                    entries = [day_text]
                elif current_day and line:
                    entries.append(line)
            if current_day:
                days.append({'day': current_day, 'text': day_text, 'entries': entries})
        return ReadingPlan(plan_id, title or Path(filepath).stem, days)

    @staticmethod
    def load_all_plans() -> Dict[str, 'ReadingPlan']:
        """
        Загружает все txt-планы из папки ./data/plans/ (или другой, если нужно).
        Возвращает словарь: короткий id (plan1, plan2, ...) -> ReadingPlan
        """
        plans = {}
        plans_dir = Path('data/plans')
        if not plans_dir.exists():
            return plans
        txt_files = sorted(plans_dir.glob('*.txt'))
        for idx, file in enumerate(txt_files, 1):
            plan_id = f"plan{idx}"
            plan_obj = ReadingPlan.parse_txt_plan(str(file), plan_id, title=file.stem)
            plans[plan_id] = plan_obj
        return plans
