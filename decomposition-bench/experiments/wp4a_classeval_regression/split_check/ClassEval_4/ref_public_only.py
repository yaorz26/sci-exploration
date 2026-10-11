class AssessmentSystem:
    def __init__(self):
        self.students = {}

    def add_student(self, name, grade, major):
        self.students[name] = {'name': name, 'grade': grade, 'major': major, 'courses': {}}

    def add_course_score(self, name, course, score):
        if name in self.students:
            self.students[name]['courses'][course] = score

    def get_gpa(self, name):
        if name in self.students and self.students[name]['courses']:
            return sum(self.students[name]['courses'].values()) / len(self.students[name]['courses'])
        else:
            return None

    def get_all_students_with_fail_course(self):
        students = []
        for name, student in self.students.items():
            for course, score in student['courses'].items():
                if score < 60:
                    students.append(name)
                    break
        return students

    def get_course_average(self, course):
        total = 0
        count = 0
        for student in self.students.values():
            if course in student['courses']:
                score = student['courses'][course]
                if score is not None:
                    total += score
                    count += 1
        return total / count if count > 0 else None

    def get_top_student(self):
        top_student = None
        top_gpa = 0
        for name, student in self.students.items():
            gpa = self.get_gpa(name)
            if gpa is not None and gpa > top_gpa:
                top_gpa = gpa
                top_student = name
        return top_student

import unittest

class AssessmentSystemTestAddStudent(unittest.TestCase):
    def test_add_student(self):
        assessment_system = AssessmentSystem()
        assessment_system.add_student("Alice", 3, "Mathematics")
        self.assertEqual(assessment_system.students["Alice"],
                         {'name': 'Alice', 'grade': 3, 'major': 'Mathematics', 'courses': {}})

    def test_add_student_2(self):
        assessment_system = AssessmentSystem()
        assessment_system.add_student("Alice", 3, "Mathematics")
        assessment_system.add_student("Bob", 2, "Science")
        self.assertEqual(assessment_system.students,
                         {'Alice': {'name': 'Alice', 'grade': 3, 'major': 'Mathematics', 'courses': {}},
                          'Bob': {'name': 'Bob', 'grade': 2, 'major': 'Science', 'courses': {}}})

    def test_add_student_3(self):
        assessment_system = AssessmentSystem()
        assessment_system.add_student("Alice", 3, "Mathematics")
        assessment_system.add_student("Bob", 2, "Science")
        assessment_system.add_student("Charlie", 4, "Chemistry")
        self.assertEqual(assessment_system.students,
                         {'Alice': {'name': 'Alice', 'grade': 3, 'major': 'Mathematics', 'courses': {}},
                          'Bob': {'name': 'Bob', 'grade': 2, 'major': 'Science', 'courses': {}},
                          'Charlie': {'name': 'Charlie', 'grade': 4, 'major': 'Chemistry', 'courses': {}}})

    def test_add_student_4(self):
        assessment_system = AssessmentSystem()
        assessment_system.add_student("Alice", 3, "Mathematics")
        assessment_system.add_student("Bob", 2, "Science")
        assessment_system.add_student("Charlie", 4, "Chemistry")
        assessment_system.add_student("David", 1, "Physics")
        self.assertEqual(assessment_system.students,
                            {'Alice': {'name': 'Alice', 'grade': 3, 'major': 'Mathematics', 'courses': {}},
                                'Bob': {'name': 'Bob', 'grade': 2, 'major': 'Science', 'courses': {}},
                                'Charlie': {'name': 'Charlie', 'grade': 4, 'major': 'Chemistry', 'courses': {}},
                                'David': {'name': 'David', 'grade': 1, 'major': 'Physics', 'courses': {}}})

    def test_add_student_5(self):
        assessment_system = AssessmentSystem()
        assessment_system.add_student("Alice", 3, "Mathematics")
        assessment_system.add_student("Bob", 2, "Science")
        assessment_system.add_student("Charlie", 4, "Chemistry")
        assessment_system.add_student("David", 1, "Physics")
        assessment_system.add_student("Eve", 3, "Mathematics")
        self.assertEqual(assessment_system.students,
                            {'Alice': {'name': 'Alice', 'grade': 3, 'major': 'Mathematics', 'courses': {}},
                                'Bob': {'name': 'Bob', 'grade': 2, 'major': 'Science', 'courses': {}},
                                'Charlie': {'name': 'Charlie', 'grade': 4, 'major': 'Chemistry', 'courses': {}},
                                'David': {'name': 'David', 'grade': 1, 'major': 'Physics', 'courses': {}},
                                'Eve': {'name': 'Eve', 'grade': 3, 'major': 'Mathematics', 'courses': {}}})

class AssessmentSystemTestAddCourseScore(unittest.TestCase):
    def test_add_course_score(self):
        assessment_system = AssessmentSystem()
        assessment_system.students = {"Alice": {'name': 'Alice', 'grade': 3, 'major': 'Mathematics', 'courses': {}}}
        assessment_system.add_course_score("Alice", "Math", 90)
        self.assertEqual(assessment_system.students["Alice"]["courses"]["Math"], 90)

    def test_add_course_score_2(self):
        assessment_system = AssessmentSystem()
        assessment_system.students["Alice"] = {'name': 'Alice', 'grade': 3, 'major': 'Mathematics', 'courses': {}}
        assessment_system.add_course_score("Alice", "Math", 90)
        self.assertEqual(assessment_system.students["Alice"]["courses"]["Math"], 90)

    def test_add_course_score_3(self):
        assessment_system = AssessmentSystem()
        assessment_system.students["Alice"] = {'name': 'Alice', 'grade': 3, 'major': 'Mathematics', 'courses': {}}
        assessment_system.add_course_score("Alice", "Math", 90)
        assessment_system.add_course_score("Alice", "Science", 80)
        assessment_system.add_course_score("Alice", "Math", 95)
        self.assertEqual(assessment_system.students["Alice"]["courses"]["Math"], 95)
        self.assertEqual(assessment_system.students["Alice"]["courses"]["Science"], 80)

    def test_add_course_score_4(self):
        assessment_system = AssessmentSystem()
        assessment_system.students["Alice"] = {'name': 'Alice', 'grade': 3, 'major': 'Mathematics', 'courses': {}}
        assessment_system.add_course_score("Alice", "Math", 90)
        assessment_system.add_course_score("Alice", "Science", 80)
        assessment_system.add_course_score("Alice", "Math", 95)
        assessment_system.add_course_score("Alice", "Science", 85)
        self.assertEqual(assessment_system.students["Alice"]["courses"]["Math"], 95)
        self.assertEqual(assessment_system.students["Alice"]["courses"]["Science"], 85)

    def test_add_course_score_5(self):
        assessment_system = AssessmentSystem()
        assessment_system.students["Alice"] = {'name': 'Alice', 'grade': 3, 'major': 'Mathematics', 'courses': {}}
        assessment_system.add_course_score("Bob", "Math", 90)
        self.assertEqual(assessment_system.students["Alice"]["courses"], {})

class AssessmentSystemTestGetGPA(unittest.TestCase):
    def test_get_gpa_1(self):
        assessment_system = AssessmentSystem()
        assessment_system.students = {'Alice': {'name': 'Alice', 'grade': 3, 'major': 'Mathematics', 'courses': {'Mathematics': 90, 'Science': 80}}}
        self.assertEqual(assessment_system.get_gpa("Alice"), 85.0)


    # No such student
    def test_get_gpa_2(self):
        assessment_system = AssessmentSystem()
        self.assertEqual(assessment_system.get_gpa('Alice'), None)

    # student don't have any scores
    def test_get_gpa_3(self):
        assessment_system = AssessmentSystem()
        assessment_system.students = {'Alice': {'name': 'Alice', 'grade': 3, 'major': 'Mathematics', 'courses': {}}}
        self.assertEqual(assessment_system.get_gpa('Alice'), None)

    def test_get_gpa_4(self):
        assessment_system = AssessmentSystem()
        assessment_system.students = {'Alice': {'name': 'Alice', 'grade': 3, 'major': 'Mathematics', 'courses': {'Mathematics': 90}}}
        self.assertEqual(assessment_system.get_gpa('Bob'), None)

    def test_get_gpa_5(self):
        assessment_system = AssessmentSystem()
        assessment_system.students = {'Alice': {'name': 'Alice', 'grade': 3, 'major': 'Mathematics', 'courses': {'Mathematics': 90}}}
        self.assertEqual(assessment_system.get_gpa('Alice'), 90.0)

if __name__ == '__main__':
    unittest.main()
