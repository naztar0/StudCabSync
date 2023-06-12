#!/usr/bin/env python
import logging
from app.utils import utils
from app.utils.database_connection import DatabaseConnection
from decimal import Decimal
from datetime import datetime


subj_exceptions = ('Військова підготовка',)

notifications = {
    'subject_mark_changed': {
        'uk': 'Змінено оцінку з предмету {subject} на {mark}',
        'ru': 'Изменена оценка по предмету {subject} на {mark}',
        'en': 'Subject {subject} mark changed to {mark}'
    },
    'subject_professor_changed': {
        'uk': 'Змінено викладача з предмету {subject} на {professor}',
        'ru': 'Изменен преподаватель по предмету {subject} на {professor}',
        'en': 'Subject {subject} professor changed to {professor}'
    },
    'rating_mark_added': {
        'uk': 'Додано рейтингову оцінку за {semester} семестр: {mark}',
        'ru': 'Добавлена рейтинговая оценка за {semester} семестр: {mark}',
        'en': 'Added rating mark for {semester} semester: {mark}',
    },
    'rating_mark_changed': {
        'uk': 'Змінено рейтингову оцінку за {semester} семестр: {mark}',
        'ru': 'Изменена рейтинговая оценка за {semester} семестр: {mark}',
        'en': 'Changed rating mark for {semester} semester: {mark}',
    },
    'contract_payment_added': {
        'uk': 'Зараховано оплату за контракт: {amount} грн.',
        'ru': 'Зачтена оплата за контракт: {amount} грн.',
        'en': 'Added contract payment: {amount} UAH',
    },
    'contract_price_changed': {
        'uk': 'Змінено вартість контракту на {price} грн.',
        'ru': 'Изменена стоимость контракта на {price} грн.',
        'en': 'Changed contract price to {price} UAH',
    }
}


def sync_profile(user, user_api):
    train_form, train_level, payment = utils.profile_convert_to_enums(user_api)

    user.first_name = user_api['imya']
    user.last_name = user_api['fam']
    user.middle_name = user_api['otch']
    user.year = user_api['kurs']
    user.train_form = train_form
    user.train_level = train_level
    user.payment = payment

    with DatabaseConnection() as db:
        conn, cursor = db
        cursor.executemany(
            "UPDATE users SET first_name=(%s), last_name=(%s), middle_name=(%s), year=(%s), train_form=(%s), train_level=(%s), payment=(%s) WHERE id=(%s)",
            [(user.first_name, user.last_name, user.middle_name, user.year, user.train_form, user.train_level,
              user.payment, user.id)]
        )
        conn.commit()


def sync_syllabus(user):
    for sem in range(1, 13):
        logging.debug(f'Semester: {sem}')
        syllabus_api = utils.get_user_syllabus(user, sem)
        if not syllabus_api:
            continue
        with DatabaseConnection() as db:
            conn, cursor = db
            cursor.execute(
                "SELECT syllabuses.id, syllabuses.subject_id, syllabuses.credit, syllabuses.control, syllabuses.individual_task, syllabuses.hours, "
                "subjects.department_id "
                "FROM syllabuses "
                "LEFT JOIN subjects ON subjects.id=syllabuses.subject_id "
                "WHERE syllabuses.group_id=(%s) AND syllabuses.semester=(%s)",
                [user.group_id, sem]
            )
            syllabus = cursor.fetchall()
        for subj in syllabus_api:
            department_name = utils.esc(subj['kafedra'])
            control, individual_task = utils.syllabus_convert_to_enums(subj)
            logging.debug(f"Subject Id: {int(subj['subj_id'])}")
            if int(subj['subj_id']) not in [x[1] for x in syllabus]:
                with DatabaseConnection() as db:
                    conn, cursor = db
                    cursor.execute("SELECT EXISTS (SELECT id FROM subjects WHERE id=(%s))", [int(subj['subj_id'])])
                    if not cursor.fetchone()[0]:
                        subject_name = utils.esc(subj['subj_name'])
                        cursor.execute("SELECT id FROM departments WHERE name=(%s)", [department_name])
                        department_id = cursor.fetchone()
                        department_id = department_id[0] if department_id else None
                        cursor.execute(
                            "INSERT INTO subjects (id, title, department_id) VALUES (%s, %s, %s)",
                            [int(subj['subj_id']), subject_name, department_id]
                        )
                        conn.commit()
                    cursor.execute(
                        "INSERT INTO syllabuses (group_id, subject_id, credit, control, individual_task, hours, semester) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        [user.group_id, int(subj['subj_id']), Decimal(subj['credit'] or 0), control, individual_task, Decimal(subj['audit'] or 0), sem]
                    )
                    conn.commit()
                continue
            for s in syllabus:
                if int(subj['subj_id']) == s[1]:
                    with DatabaseConnection() as db:
                        conn, cursor = db
                        if s[2] != Decimal(subj['credit'] or 0) or s[3] != control or s[4] != individual_task or s[5] != Decimal(subj['audit'] or 0):
                            cursor.execute(
                                "UPDATE syllabuses SET credit=(%s), control=(%s), individual_task=(%s), hours=(%s) WHERE id=(%s)",
                                [Decimal(subj['credit'] or 0), control, individual_task, Decimal(subj['audit'] or 0), s[0]]
                            )
                            conn.commit()
                        if not s[6]:
                            cursor.execute("SELECT id FROM departments WHERE name=(%s)", [department_name])
                            department_id = cursor.fetchone()
                            department_id = department_id[0] if department_id else None
                            if department_id:
                                cursor.execute(
                                    "UPDATE subjects SET department_id=(%s) WHERE id=(%s)",
                                    [department_id, int(subj['subj_id'])]
                                )
                            conn.commit()
                    break
        for s in syllabus:
            if s[1] not in [int(x['subj_id']) for x in syllabus_api]:
                with DatabaseConnection() as db:
                    conn, cursor = db
                    cursor.execute("DELETE FROM syllabuses WHERE id=(%s)", [s[0]])
                    conn.commit()


class RecordBookWithSyllabusWithSubjects:
    def __init__(self, data):
        self.record_book_id, self.record_book_syllabus_id, self.record_book_mark_id, self.record_book_mark, \
            self.record_book_debt_date, self.record_book_user_id, \
            self.syllabus_id, self.syllabus_subject_id, \
            self.subject_id, self.subject_title, self.subject_professor_name, self.subject_professor_id = data
        self.subject_title = utils.esc(self.subject_title)
        self.subject_professor_name = utils.esc(self.subject_professor_name)


def get_record_book_syllabus_subjects(group_id, semester):
    query = "SELECT record_books.id, record_books.syllabus_id, record_books.mark_id, record_books.mark, record_books.debt_date, record_books.user_id, " \
            "syllabuses.id, syllabuses.subject_id, " \
            "subjects.id, subjects.title, subjects.professor_name, subjects.professor_id " \
            "FROM record_books " \
            "RIGHT JOIN syllabuses ON record_books.syllabus_id=syllabuses.id " \
            "LEFT JOIN subjects ON syllabuses.subject_id=subjects.id " \
            "WHERE syllabuses.group_id=(%s) AND syllabuses.semester=(%s)"
    params = [group_id, semester]
    with DatabaseConnection() as db:
        conn, cursor = db
        cursor.execute(query, params)
        result = cursor.fetchall()
    return [RecordBookWithSyllabusWithSubjects(x) for x in result]


def sync_record_book(user):
    debts = utils.get_user_debts(user)
    if not debts:
        return
    debts_ids = [x['oc_id'] for x in debts]
    for sem in range(1, 13):
        logging.debug(f'Semester: {sem}')
        record_book_api = utils.get_user_record_book(user, sem)
        if not record_book_api:
            continue
        result = get_record_book_syllabus_subjects(user.group_id, sem)
        for subj in record_book_api:
            subject_name = utils.esc(subj['subject'])
            if not subject_name or (not subj['oc_bol'] and (not subj['oc_id'] in debts_ids or subject_name in subj_exceptions)):
                continue
            logging.debug(f'Subject name: {subject_name}')
            subject_names = [x.subject_title for x in result]
            if subject_name not in subject_names:
                for s in result:
                    if s.subject_title.split()[0] == 'Дисципліна':
                        logging.debug(f'! Exception; Subject name: {subject_name}')
                        with DatabaseConnection() as db:
                            conn, cursor = db
                            cursor.execute(
                                "UPDATE subjects SET title=(%s) WHERE id=(%s)",
                                [subject_name, s.subject_id]
                            )
                            conn.commit()
                        break
            record_book_subject_names = [x.subject_title for x in result if x.record_book_id and x.record_book_user_id == user.id]
            debt_date = None
            try:
                debt_api_date = debts[debts_ids.index(subj['oc_id'])]['data']
            except ValueError:
                debt_api_date = None
            if subj['oc_id'] in debts_ids:
                if subj['data'] or debt_api_date:
                    debt_date = datetime.strptime(subj['data'] or debt_api_date, '%d.%m.%Y').date()
                else:
                    debt_date = datetime.now().date()
            if subject_name not in record_book_subject_names:
                for s in result:
                    if s.subject_title == subject_name:
                        logging.debug(f'? New; Subject name: {subject_name}')
                        with DatabaseConnection() as db:
                            conn, cursor = db
                            cursor.execute(
                                "INSERT INTO record_books (user_id, syllabus_id, mark_id, mark, debt_date) VALUES (%s, %s, %s, %s, %s)",
                                [user.id, s.syllabus_id, subj['oc_id'], subj['oc_bol'], debt_date]
                            )
                            conn.commit()
                        break
            result = get_record_book_syllabus_subjects(user.group_id, sem)
            for s in result:
                if s.record_book_user_id == user.id and s.subject_title == subject_name:
                    if s.record_book_mark_id != subj['oc_id'] or s.record_book_mark != subj['oc_bol'] or s.record_book_debt_date != debt_date:
                        with DatabaseConnection() as db:
                            conn, cursor = db
                            cursor.execute(
                                "UPDATE record_books SET mark_id=(%s), mark=(%s), debt_date=(%s) WHERE id=(%s)",
                                [subj['oc_id'], subj['oc_bol'], debt_date, s.record_book_id]
                            )
                            cursor.execute(
                                "INSERT INTO notifications (user_id, text) VALUES (%s, %s)",
                                [user.id, notifications['subject_mark_changed'][user.locale].format(subject=s.subject_title, mark=subj['oc_bol'])],
                            )
                            conn.commit()
                    name = utils.Name()
                    name.parse(utils.esc(subj['prepod']))
                    if name:
                        if not s.subject_professor_name:
                            with DatabaseConnection() as db:
                                conn, cursor = db
                                cursor.execute(
                                    "UPDATE subjects SET professor_name=(%s) WHERE id=(%s)",
                                    [str(name), s.subject_id]
                                )
                                cursor.execute(
                                    "INSERT INTO notifications (user_id, text) VALUES (%s, %s)",
                                    [user.id, notifications['subject_professor_changed'][user.locale].format(subject=s.subject_title, professor=name)],
                                )
                                conn.commit()
                        if not s.subject_professor_id:
                            with DatabaseConnection() as db:
                                conn, cursor = db
                                cursor.execute(
                                    "SELECT id FROM users WHERE last_name=(%s) AND first_name LIKE (%s) AND middle_name LIKE (%s) AND role='professor'",
                                    [name.last_name, name.first_name + '%', name.middle_name + '%']
                                )
                                professor_id = cursor.fetchone()
                                if professor_id:
                                    cursor.execute(
                                        "UPDATE subjects SET professor_id=(%s) WHERE id=(%s)",
                                        [professor_id[0], s.subject_id]
                                    )
                                    conn.commit()
                    break


def sync_rating(user):
    with DatabaseConnection() as db:
        conn, cursor = db
        cursor.execute("SELECT speciality_id FROM programs WHERE id=("
                       "SELECT program_id FROM departments WHERE id=("
                       "SELECT department_id FROM specializations WHERE id=("
                       "SELECT specialization_id FROM `groups` WHERE id=(%s))))",
                       [user.group_id])
        speciality_id = cursor.fetchone()[0]
    for sem in range(1, 13):
        rating_api = utils.get_user_rating(user, sem)
        if not rating_api:
            continue
        with DatabaseConnection() as db:
            conn, cursor = db
            cursor.execute(
                "SELECT ratings.id, ratings.mark, ratings.comment, users.student_id, ratings.student_id, ratings.user_id "
                "FROM ratings "
                "LEFT JOIN users ON users.id=ratings.user_id "
                "LEFT JOIN `groups` ON `groups`.id=users.group_id "
                "LEFT JOIN specializations ON specializations.id=`groups`.specialization_id "
                "LEFT JOIN departments ON departments.id=specializations.department_id "
                "LEFT JOIN programs ON programs.id=departments.program_id "
                "LEFT JOIN specialities ON specialities.id=programs.speciality_id "
                "WHERE ratings.semester=(%s) AND (specialities.id=(%s) OR ratings.speciality_id=(%s))",
                [sem, speciality_id, speciality_id]
            )
            ratings = cursor.fetchall()
        students_ids: list[int] = [x[3] or x[4] for x in ratings]
        for u in rating_api:
            stud_id = u['studid']
            comment = u['rating'].replace('*', ' × ').replace('[', '(').replace(']', ')') if u['rating'] else None
            mark = round(Decimal(u['sbal100'] or 0), 2)
            with DatabaseConnection() as db:
                conn, cursor = db
                cursor.execute("SELECT id FROM users WHERE student_id=(%s)", [stud_id])
                user_id = cursor.fetchone()
                user_id = user_id[0] if user_id else None
            if stud_id not in students_ids:
                if user_id:
                    logging.debug(f'Registered user {user_id} rating not in database')
                    with DatabaseConnection() as db:
                        conn, cursor = db
                        cursor.execute(
                            "INSERT INTO ratings (user_id, semester, mark, `comment`) VALUES (%s, %s, %s, %s)",
                            [user_id, sem, mark, comment]
                        )
                        if user_id == user.id:
                            cursor.execute(
                                "INSERT INTO notifications (user_id, text) VALUES (%s, %s)",
                                [user_id, notifications['rating_mark_added'][user.locale].format(semester=sem, mark=mark)],
                            )
                        conn.commit()
                else:
                    logging.debug(f'Unregistered user {stud_id} rating not in database')
                    name = utils.Name()
                    name.parse(utils.esc(u['fio']))
                    if stud_id not in students_ids:
                        with DatabaseConnection() as db:
                            conn, cursor = db
                            cursor.execute(
                                "INSERT INTO ratings (name, student_id, speciality_id, `group`, semester, mark, `comment`) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                [str(name), stud_id, speciality_id, u['gabr'], sem, mark, comment]
                            )
                            conn.commit()
            else:
                rating = ratings[students_ids.index(stud_id)]
                if rating[1] != mark or rating[2] != comment or user_id != rating[5]:
                    logging.debug(f'User {user_id} rating changed, mark: {rating[1]} -> {mark}, comment: {rating[2]} -> {comment}')
                    with DatabaseConnection() as db:
                        conn, cursor = db
                        cursor.execute(
                            "UPDATE ratings SET user_id=(%s), mark=(%s), `comment`=(%s) WHERE id=(%s)",
                            [user_id, mark, comment, rating[0]]
                        )
                        if user_id == user.id:
                            cursor.execute(
                                "INSERT INTO notifications (user_id, text) VALUES (%s, %s)",
                                [user_id, notifications['rating_mark_changed'][user.locale].format(semester=sem, mark=mark)],
                            )
                        conn.commit()


def sync_payments(user):
    payments_api = utils.get_user_payments(user)
    if not payments_api:
        return
    with DatabaseConnection() as db:
        conn, cursor = db
        cursor.execute(
            "SELECT payments.id, contracts.price "
            "FROM payments "
            "LEFT JOIN contracts ON contracts.id=payments.contract_id "
            "WHERE contracts.user_id=(%s)",
            [user.id]
        )
        payments = cursor.fetchall()
    for payment in payments_api:
        logging.debug(f"Payment Id: {payment['dp_id']}")
        if int(payment['dp_id']) not in [x[0] for x in payments]:
            with DatabaseConnection() as db:
                conn, cursor = db
                cursor.execute("SELECT EXISTS (SELECT id FROM contracts WHERE id=(%s))", [int(payment['dog_id'])])
                if not cursor.fetchone()[0]:
                    created_at = datetime.strptime(payment['start_date'], '%d.%m.%Y')
                    cursor.execute(
                        "INSERT INTO contracts (id, title, price, user_id, created_at) VALUES (%s, %s, %s, %s, %s)",
                        [int(payment['dog_id']), payment['dog_name'], int(payment['dog_price']), user.id, created_at]
                    )
                    conn.commit()
                created_at = datetime.strptime(payment['paid_date'], '%d.%m.%Y')
                cursor.execute(
                    "INSERT INTO payments (id, contract_id, amount, semester, created_at) VALUES (%s, %s, %s, %s, %s)",
                    [int(payment['dp_id']), int(payment['dog_id']), int(payment['paid_value']), int(payment['term_start']), created_at]
                )
                cursor.execute(
                    "INSERT INTO notifications (user_id, text) VALUES (%s, %s)",
                    [user.id, notifications['contract_payment_added'][user.locale].format(amount=payment['paid_value'])],
                )
                conn.commit()
            continue
    if not payments:
        return
    payment = payments_api[0]
    if int(payment['dog_price']) != payments[0][1]:
        logging.debug(f"Changed price: {payments[0][1]} -> {int(payment['dog_price'])}")
        with DatabaseConnection() as db:
            conn, cursor = db
            cursor.execute(
                "UPDATE contracts SET price=(%s) WHERE id=(%s)",
                [int(payment['dog_price']), int(payment['dog_id'])]
            )
            cursor.execute(
                "INSERT INTO notifications (user_id, text) VALUES (%s, %s)",
                [user.id, notifications['contract_price_changed'][user.locale].format(price=int(payment['dog_price']))],
            )
            conn.commit()
