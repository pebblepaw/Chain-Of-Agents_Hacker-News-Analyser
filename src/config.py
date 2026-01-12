# from typing import List, Dict
from datetime import datetime, timedelta

class ChainConfig: 
    MODEL_NAME = 'gemini-2.5-flash'
    TEMPERATURE = 0.3  # lower = more deterministic
    MAX_STEPS = 5  # max reasoning steps for agents

    # HN Search Tool Config
    HN_SEARCH_LIMIT = 10  # default number of stories to fetch per search

    @staticmethod 
    def get_default_time_periods() -> list[dict[str,str]]: 
        """Returns default time periods for analysis."""
        return [
            {"start": "2024-01-01", "end": "2024-03-31", "label": "Q1 2024"},
            {"start": "2024-04-01", "end": "2024-06-30", "label": "Q2 2024"},
            {"start": "2024-07-01", "end": "2024-09-30", "label": "Q3 2024"},
            {"start": "2024-10-01", "end": "2024-12-31", "label": "Q4 2024"},
        ]
    
    @staticmethod 
    def get_monthly_periods(year:int, month_start:int, month_end:int) -> list[dict[str,str]]:
        periods = []    
        for month in range(month_start, month_end + 1):

            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            periods.append({
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
                "label": start_date.strftime("%B %Y")
            })

        return periods
    