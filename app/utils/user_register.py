#!/usr/bin/env python
from app.utils.database_connection import DatabaseConnection
from app.utils.utils import esc, profile_convert_to_enums


def register_user(user, email, password):
    with DatabaseConnection() as db:
        conn, cursor = db
        cursor.execute("SELECT id FROM faculties WHERE id=%s", [user['fid']])
        faculty = cursor.fetchone()
        if not faculty:
            cursor.executemany("INSERT INTO faculties (id, name) VALUES (%s, %s)", [(user['fid'], esc(user['fakultet']))])
            conn.commit()
            cursor.execute("SELECT id FROM faculties WHERE id=%s", [user['fid']])
            faculty = cursor.fetchone()
        cursor.execute("SELECT id FROM specialities WHERE name=%s", [esc(user['speciality'])])
        speciality = cursor.fetchone()
        if not speciality:
            cursor.executemany("INSERT INTO specialities (name, faculty_id) VALUES (%s, %s)", [(esc(user['speciality']), faculty[0])])
            conn.commit()
            cursor.execute("SELECT id FROM specialities WHERE name=%s", [esc(user['speciality'])])
            speciality = cursor.fetchone()
        cursor.execute("SELECT id FROM programs WHERE name=%s", [esc(user['osvitprog'])])
        program = cursor.fetchone()
        if not program:
            cursor.executemany("INSERT INTO programs (name, speciality_id) VALUES (%s, %s)", [(esc(user['osvitprog']), speciality[0])])
            conn.commit()
            cursor.execute("SELECT id FROM programs WHERE name=%s", [esc(user['osvitprog'])])
            program = cursor.fetchone()
        cursor.execute("SELECT id FROM departments WHERE id=%s", [user['kid']])
        department = cursor.fetchone()
        if not department:
            cursor.executemany("INSERT INTO departments (id, name, program_id) VALUES (%s, %s, %s)", [(user['kid'], esc(user['kafedra']), program[0])])
            conn.commit()
            cursor.execute("SELECT id FROM departments WHERE id=%s", [user['kid']])
            department = cursor.fetchone()
        cursor.execute("SELECT id FROM specializations WHERE name=%s", [esc(user['specialization'])])
        specialization = cursor.fetchone()
        if not specialization:
            cursor.executemany("INSERT INTO specializations (name, department_id) VALUES (%s, %s)", [(esc(user['specialization']), department[0])])
            conn.commit()
            cursor.execute("SELECT id FROM specializations WHERE name=%s", [esc(user['specialization'])])
            specialization = cursor.fetchone()
        cursor.execute("SELECT id FROM `groups` WHERE id=%s", [user['gid']])
        group = cursor.fetchone()
        if not group:
            cursor.executemany("INSERT INTO `groups` (id, name, specialization_id) VALUES (%s, %s, %s)", [(user['gid'], esc(user['grupa']), specialization[0])])
            conn.commit()
            cursor.execute("SELECT id FROM `groups` WHERE id=%s", [user['gid']])
            group = cursor.fetchone()

        train_form, train_level, payment = profile_convert_to_enums(user)

        cursor.executemany("INSERT INTO users (email, pass, first_name, last_name, middle_name, student_id, group_id, year, train_form, train_level, payment) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                           [(email.lower(), password, esc(user['imya']), esc(user['fam']), esc(user['otch']), user['st_cod'], group[0], user['kurs'], train_form, train_level, payment)])
        conn.commit()

        return cursor.lastrowid
