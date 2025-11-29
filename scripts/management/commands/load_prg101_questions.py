from django.core.management.base import BaseCommand
from django.db import transaction
from course.models import Program, Course
from quiz.models import Quiz, MCQuestion, Choice
import random


class Command(BaseCommand):
    help = 'Load 30 sample MC questions for each course'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to load sample questions for all courses...'))

        courses = Course.objects.all()
        if not courses:
            self.stdout.write(self.style.WARNING('No courses found. Please create some courses first.'))
            return

        for course in courses:
            with transaction.atomic():
                quiz_title = f'{course.code} Quiz'
                quiz, created_quiz = Quiz.objects.get_or_create(
                    course=course,
                    title=quiz_title,
                    defaults={
                        'description': f'Sample quiz for {course.title}',
                        'category': 'practice',
                        'pass_mark': 50
                    }
                )
                if created_quiz:
                    self.stdout.write(self.style.SUCCESS(f'Created quiz: {quiz.title} for {course}'))
                else:
                    # Check if questions already exist
                    if quiz.question_set.exists():
                        self.stdout.write(self.style.WARNING(f'Questions already exist for {quiz.title}, skipping...'))
                        continue
                    else:
                        self.stdout.write(self.style.WARNING(f'Clearing existing questions from quiz: {quiz.title}'))

                # Load 30 sample questions
                questions_data = self.generate_sample_questions(course)
                for i, q_data in enumerate(questions_data, 1):
                    if q_data['type'] == 'mc':
                        question = MCQuestion.objects.create(
                            content=q_data['content'],
                            explanation=q_data.get('explanation', ''),
                            choice_order='content'
                        )
                        # Create choices
                        for choice_text, is_correct in q_data['choices']:
                            Choice.objects.create(
                                question=question,
                                choice_text=choice_text,
                                correct=is_correct
                            )
                        quiz.question_set.add(question)

                    self.stdout.write(self.style.SUCCESS(f'Added question {i}: {question.content[:50]}...'))

                self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(questions_data)} questions for {course}'))

        self.stdout.write(self.style.SUCCESS('All courses have been loaded with sample questions.'))

    def generate_sample_questions(self, course):
        """Generate 30 sample MC questions"""
        questions = []

        # Basic programming concepts
        basic_questions = [
            {
                'type': 'mc',
                'content': "What is a variable in programming?",
                'choices': [
                    ("A type of data storage", True),
                    ("A mathematical equation", False),
                    ("A loop structure", False),
                    ("A function definition", False),
                ]
            },
            {
                'type': 'mc',
                'content': "Which keyword is used to declare a function in Python?",
                'choices': [
                    ("def", True),
                    ("var", False),
                    ("function", False),
                    ("method", False),
                ]
            },
            {
                'type': 'mc',
                'content': "What does the 'if' statement do?",
                'choices': [
                    ("Executes code conditionally", True),
                    ("Repeats code", False),
                    ("Defines a function", False),
                    ("Outputs text", False),
                ]
            },
            {
                'type': 'mc',
                'content': "How do you create a list in Python?",
                'choices': [
                    ("[] or list()", True),
                    ("()", False),
                    ("{}", False),
                    ("<>", False),
                ]
            },
            {
                'type': 'mc',
                'content': "What will `print(2 + 3)` output?",
                'choices': [
                    ("5", True),
                    ("23", False),
                    ("Error", False),
                    ("print(2 + 3)", False),
                ]
            },
        ]

        questions.extend(basic_questions)

        # Generate 25 more questions based on templates
        templates = self.get_question_templates(course)
        for i in range(25):
            template = random.choice(templates)
            questions.append(template)

        return questions[:30]

    def get_question_templates(self, course):
        """Get question templates"""
        num1 = random.randint(1,10)
        num2 = random.randint(1,10)
        correct_sum = num1 + num2
        choices = [
            str(correct_sum),  # Always include correct
            str(random.randint(2,20)),
            str(random.randint(2,20)),
            str(random.randint(2,20))
        ]
        random.shuffle(choices)
        return [
            # Basic math
            {
                'type': 'mc',
                'content': f'What is the result of {num1} + {num2} in Python?',
                'choices': [(choice, choice == str(correct_sum)) for choice in choices],
                'explanation': 'Basic arithmetic operation.'
            },
            # Boolean logic
            {
                'type': 'mc',
                'content': "What is the value of True and False?",
                'choices': [
                    ("False", True),
                    ("True", False),
                    ("None", False),
                    ("Error", False),
                ]
            },
            # Strings
            {
                'type': 'mc',
                'content': 'What does "Hello" + " World" result in?',
                'choices': [
                    ('"Hello World"', True),
                    ('"HelloWorld"', False),
                    ("Error", False),
                    ("None", False),
                ]
            },
            # Lists
            {
                'type': 'mc',
                'content': "How do you get the length of a list named `my_list`?",
                'choices': [
                    ("len(my_list)", True),
                    ("length(my_list)", False),
                    ("my_list.length()", False),
                    ("size(my_list)", False),
                ]
            },
            # Functions
            {
                'type': 'mc',
                'content': "What does the 'return' keyword do in a function?",
                'choices': [
                    ("Exits the function and optionally returns a value", True),
                    ("Prints output", False),
                    ("Defines a variable", False),
                    ("Creates a loop", False),
                ]
            },
            # Loops
            {
                'type': 'mc',
                'content': "Which loop type is used when the number of iterations is known?",
                'choices': [
                    ("for", True),
                    ("while", False),
                    ("if", False),
                    ("def", False),
                ]
            },
            # Dictionaries
            {
                'type': 'mc',
                'content': "How do you access a value in a dictionary by its key?",
                'choices': [
                    ("dict[key]", True),
                    ("dict.key", False),
                    ("dict(key)", False),
                    ("get(dict, key)", False),
                ]
            },
            # Classes
            {
                'type': 'mc',
                'content': "What keyword is used to define a class in Python?",
                'choices': [
                    ("class", True),
                    ("def", False),
                    ("var", False),
                    ("object", False),
                ]
            },
        ]
