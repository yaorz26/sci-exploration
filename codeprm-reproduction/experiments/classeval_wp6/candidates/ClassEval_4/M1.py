class AssessmentSystem:
    def __init__(self):
        self.students = {}

    def add_student(self, name, grade, major):
        if name in self.students:
            self.students[name].update({'grade': grade, 'major': major})
        else:
            self.students[name] = {'name': name, 'grade': grade, 'major': major, 'courses': {}}

    def add_course_score(self, name, course, score):
        if name not in self.students:
            self.add_student(name, None, None)
        self.students[name]['courses'][course] = score

    def get_gpa(self, name):
        if name in self.students and self.students[name]['courses']:
            total_score = sum(self.students[name]['courses'].values())
            num_courses = len(self.students[name]['courses'])
            return total_score / num_courses
        return None

    def get_all_students_with_fail_course(self):
        return [name for name, student in self.students.items() if any(score < 60 for score in student['courses'].values())]

    def get_course_average(self, course):
        scores = [student['courses'].get(course) for student in self.students.values() if course in student['courses']]
        if scores:
            return sum(scores) / len(scores)
        return None

    def get_top_student(self):
        top_student = None
        highest_gpa = None
        for name, student in self.students.items():
            gpa = self.get_gpa(name)
            if gpa is not None and (highest_gpa is None or gpa > highest_gpa):
                top_student = name
                highest_gpa = gpa
        return top_student