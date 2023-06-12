import json
import requests
from contextlib import suppress
from app import misc
from app.utils.database_connection import DatabaseConnection


class Student:
    def __init__(self, args):
        self.id, \
            self.student_id, \
            self.telegram_id, \
            self.azure_id, \
            self.group_id, \
            self.email, \
            self.password, \
            self.first_name, \
            self.last_name, \
            self.middle_name, \
            self.role, \
            self.image, \
            self.cover, \
            self.locale, \
            self.year, \
            self.train_level, \
            self.train_form, \
            self.payment, \
            self.created_at, \
            self.updated_at = args

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def __bool__(self):
        return bool(self.id)


class Name:
    def __init__(self, first_name=None, last_name=None, middle_name=None):
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.middle_name: str = middle_name

    def parse(self, s: str):
        if not s:
            return
        name_split = s.split()
        self.last_name = name_split[0].capitalize()
        if len(name_split) == 3:
            self.first_name = name_split[1][0].upper()
            self.middle_name = name_split[2][0].upper()
        elif len(name_split) == 2:
            tmp = name_split[1].split('.')
            self.first_name = tmp[0][0].upper()
            self.middle_name = tmp[1][0].upper() if len(tmp) > 1 else ''

    def __bool__(self):
        return bool(self.first_name and self.last_name)

    def __str__(self):
        if self and self.middle_name:
            return f'{self.last_name} {self.first_name[0]}. {self.middle_name[0]}.'
        elif self:
            return f'{self.last_name} {self.first_name[0]}.'
        return ''


def req_post(url, method='POST', **kwargs):
    try:
        if method == 'POST':
            response = requests.post(url, timeout=20, **kwargs)
        elif method == 'GET':
            response = requests.get(url, timeout=10, **kwargs)
        else:
            return
    except (requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError):
        return
    return response


def get_update_json(filename, key=None, value=None):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not key:
        return data
    if not value:
        return data.get(key)
    data[key] = value
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


def api_request(params=None, url=misc.api_url_v2, student=None) -> dict | None:
    if url == misc.api_url_v2:
        _json = (params or {}) | misc.api_required_params
        if student:
            _json['marks'] = generate_hash_array(student)
        response = req_post(url, json=_json)
    else:
        response = req_post(url, params=params)
    if response:
        with suppress(json.decoder.JSONDecodeError):
            return response.json()


def get_user_profile(student: Student) -> dict | None:
    return api_request({'email': student.email, 'pass': student.password, 'page': 1})


def get_user_record_book(student: Student, semester: int) -> dict | None:
    return api_request({'email': student.email, 'pass': student.password, 'page': 2, 'semester': semester}, student=student)


def get_user_debts(student: Student) -> dict | None:
    return api_request({'email': student.email, 'pass': student.password, 'page': 3}, student=student)


def get_user_syllabus(student: Student, semester: int) -> dict | None:
    return api_request({'email': student.email, 'pass': student.password, 'page': 4, 'semester': semester}, student=student)


def get_user_rating(student: Student, semester: int) -> dict | None:
    return api_request({'email': student.email, 'pass': student.password, 'page': 5, 'semester': semester}, student=student)


def get_user_payments(student: Student) -> dict | None:
    return api_request({'email': student.email, 'pass': student.password, 'page': 6}, student=student)


def generate_hash_array(student: Student) -> tuple[int]:
    code1 = int(str(student.student_id)[0] + str(student.student_id)[2] + str(student.student_id)[4])
    code2 = int(str(student.group_id)[1:4])
    result = tuple(code2 for _ in range(code1))
    return result


def get_users(count=10, offset=0, **kwargs) -> tuple[Student]:
    findQuery = "SELECT id, student_id, telegram_id, azure_id, group_id, email, pass, first_name, last_name, middle_name, role, image, cover, locale, year, train_level, train_form, payment, created_at, updated_at " \
                "FROM users WHERE {} ORDER BY id LIMIT %s OFFSET %s"
    where = ' AND '.join(f'{key}=(%s)' for key in kwargs) or '1=1'
    values = list(kwargs.values()) + [count, offset]
    with DatabaseConnection() as db:
        conn, cursor = db
        cursor.execute(findQuery.format(where), values)
        users = cursor.fetchall()
    return tuple(Student(user) for user in users)


def get_user(user_id) -> Student | None:
    findQuery = "SELECT id, student_id, telegram_id, azure_id, group_id, email, pass, first_name, last_name, middle_name, role, image, cover, locale, year, train_level, train_form, payment, created_at, updated_at " \
                "FROM users WHERE id=(%s)"
    with DatabaseConnection() as db:
        conn, cursor = db
        cursor.execute(findQuery, [user_id])
        user = cursor.fetchone()
    if user:
        return Student(user)


def get_users_count(**kwargs) -> int:
    findQuery = "SELECT COUNT(*) FROM users WHERE {}"
    where = ' AND '.join(f'{key}=(%s)' for key in kwargs) or '1=1'
    values = list(kwargs.values())
    with DatabaseConnection() as db:
        conn, cursor = db
        cursor.execute(findQuery.format(where), values)
        count = cursor.fetchone()[0]
    return count


def esc(s: str) -> str:
    if not s:
        return ''
    return ' '.join(s.split()).replace('`', "'").replace('’', "'").strip()


def profile_convert_to_enums(user):
    train_form = None
    if user['train_form'] == 'Денна':
        train_form = 1
    elif user['train_form'] == 'Заочна':
        train_form = 2

    train_level = None
    if user['train_level'] == 'Бакалавр':
        train_level = 1
    elif user['train_level'] == 'Магістр':
        train_level = 2

    payment = None
    if user['oplata'] == 'Бюджет':
        payment = 1
    elif user['oplata'] == 'Контракт':
        payment = 2

    return train_form, train_level, payment


def syllabus_convert_to_enums(syllabus):
    control = None
    if syllabus['control'] == 'Е':
        control = 1
    elif syllabus['control'] == 'З':
        control = 2

    individual_task = None
    if syllabus['indzav'] == 'КП':
        individual_task = 1
    elif syllabus['indzav'] == 'РЕ':
        individual_task = 2
    elif syllabus['indzav'] == 'Р':
        individual_task = 3

    return control, individual_task
