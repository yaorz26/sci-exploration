class AssessmentSystem:
    """
    This is a class as an student assessment system, which supports add student, add course score, calculate GPA, and other functions for students and courses.
    """

    def __init__(self):
        """
        Initialize the students dict in assessment system.
        """
        self.students = {}

    def add_student(self, name, grade, major):
        """
        Add a new student into self.students dict
        :param name: str, student name
        :param grade: int, student grade
        :param major: str, student major
        >>> system.add_student('student 1', 3, 'SE')
        >>> system.students
        {'student 1': {'name': 'student 1', 'grade': 3, 'major': 'SE', 'courses': {}}}
        """
        self.students[name] = {'name': name, 'grade': grade, 'major': major, 'courses': {}}

    def add_course_score(self, name, course, score):
        """
        Add score of specific course for student in self.students
        :param name: str, student name
        :param course: str, course name
        :param score: int, course score
        >>> system.add_student('student 1', 3, 'SE')
        >>> system.add_course_score('student 1', 'math', 94)
        >>> system.students
        {'student 1': {'name': 'student 1', 'grade': 3, 'major': 'SE', 'courses': {'math': 94}}}
        """
        if name in self.students:
            self.students[name]['courses'][course] = score

    def get_gpa(self, name):
        """
        Get average grade of one student.
        :param name: str, student name
        :return: if name is in students and this students have courses grade, return average grade(float)
                    or None otherwise
        >>> system.add_student('student 1', 3, 'SE')
        >>> system.add_course_score('student 1', 'math', 94)
        >>> system.add_course_score('student 1', 'Computer Network', 92)
        >>> system.get_gpa('student 1')
        93.0
        """
        if name in self.students and self.students[name]['courses']:
            total_score = sum(self.students[name]['courses'].values())
            num_courses = len(self.students[name]['courses'])
            return total_score / num_courses
        else:
            return None

    def get_all_students_with_fail_course(self):
        """
        Get all students who have any score blow 60
        :return: list of str ,student name
        """
        failed_students = []
        for student, data in self.students.items():
            for course, score in data['courses'].items():
                if score < 60:
                    failed_students.append(student)
                    break
        return list(set(failed_students))

    def get_course_average(self, course):
        """
        Get the average score of a specific course.
        :param course: str, course name
        :return: float, average scores of this course if anyone have score of this course, or None if nobody have records.
        """
        scores = [student['courses'].get(course) for student in self.students.values() if course in student['courses']]
        if not scores:
            return None
        return sum(scores) / len(scores)

    def get_top_student(self):
        """
        Calculate every student's gpa with get_gpa method, and find the student with highest gpa
        :return: str, name of student whose gpa is highest
        """
        if not self.students:
            return None

        top_student = None
        highest_gpa = float('-inf')

        for student_name, student_info in self.students.items():
            student_gpa = self.get_gpa(student_name)
            if student_gpa is not None and student_gpa > highest_gpa:
                highest_gpa = student_gpa
                top_student = student_name

        return top_student
