import logging
import config
from pathlib import Path


app_dir: Path = Path(__file__).parent.parent
locales_dir = app_dir / "locales"
temp_dir = app_dir / "temp"

if config.DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.WARNING)


api_url_v1 = "https://schedule.kpi.kharkov.ua/json"
api_url_v2 = "https://cabinet.kpi.kharkov.ua/servlets/servlet_kab_stud.php"
api_sport = api_url_v1 + "/sport"
api_sched = api_url_v1 + "/Schedule"
api_doc = api_url_v1 + "/getpdf"

api_required_params = {"fio_student": "快是慢，慢是快"}

para_name = ('Para1', 'Para2', 'Para3', 'Para4', 'Para5', 'Para6')
day_names_api_match = ('Понеділок', 'Вівторок', 'Середа', 'Четвер', 'П`ятниця', 'Субота', 'Неділя')
