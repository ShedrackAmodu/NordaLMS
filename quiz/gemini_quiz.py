import json
import random
import logging
from django.conf import settings
from django.core.cache import cache
from groq import Groq

logger = logging.getLogger(__name__)

class GroqQuizGenerator:
    def __init__(self, model=None):
        self.model = model or getattr(settings, 'GROQ_MODELS', {}).get('quiz_generation', 'llama3-70b-8192')
        self.client = self._initialize_client()

    def _initialize_client(self):
        """Initialize Groq client with proper error handling"""
        api_key = getattr(settings, 'GROQ_API_KEY', "")

        if not api_key:
            logger.error("GROQ_API_KEY not found in settings")
            raise ValueError("Groq API key not configured. Please set GROQ_API_KEY in your environment variables.")

        try:
            client = Groq(api_key=api_key)
            # Test connection with a simple request
            test_response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Say 'OK'"}],
                max_tokens=5
            )
            logger.info("Groq client initialized successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            raise

    def generate_questions(self, course, difficulty, num_questions, question_types, topics=""):
        """Generate quiz questions with caching and retry logic"""

        # Create cache key based on parameters
        cache_key = f"quiz_{course.id}_{difficulty}_{num_questions}_{'_'.join(question_types)}_{topics}"
        cached_questions = cache.get(cache_key)

        if cached_questions:
            logger.info(f"Returning cached questions for {cache_key}")
            return cached_questions[:num_questions]

        try:
            prompt = self._build_prompt(course, difficulty, num_questions, question_types, topics)
            logger.info(f"Generating {num_questions} questions for course: {course.title}")

            messages = [{"role": "user", "content": prompt}]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=4000,
                timeout=30  # 30 second timeout
            )

            response_text = response.choices[0].message.content
            logger.debug(f"Raw Groq response: {response_text[:200]}...")

            if not response_text:
                raise ValueError("Empty response from Groq API")

            questions = self._parse_response(response_text)
            logger.info(f"Successfully parsed {len(questions)} questions")

            # Cache successful results for 1 hour
            if questions:
                cache.set(cache_key, questions, 3600)

            return questions[:num_questions]

        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            # Return fallback questions but don't cache them
            return self._get_fallback_questions(num_questions)

    def _build_prompt(self, course, difficulty, num_questions, question_types, topics):
        """Build a comprehensive and context-aware prompt for quiz generation."""
        # Ensure question_types is a list
        if isinstance(question_types, str):
            question_types = [question_types]

        # Extract rich course context
        course_context = self._extract_course_context(course)

        # Build difficulty-specific guidelines
        difficulty_guidelines = self._get_difficulty_guidelines(difficulty)

        # Prepare question type specifications
        question_specs = self._get_question_type_specifications(question_types)

        # Build topic-specific focus
        topic_focus = self._build_topic_focus(topics, course_context)

        prompt = f"""# AI QUIZ GENERATION TASK

## COURSE CONTEXT
{course_context}

## QUIZ CONFIGURATION
- Difficulty Level: {difficulty}
- Number of Questions: {num_questions} (MUST generate exactly this many)
- Question Types: {', '.join(question_types)}
{topic_focus}

## DIFFICULTY GUIDELINES
{difficulty_guidelines}

## QUESTION FORMAT REQUIREMENTS
{question_specs}

## QUALITY STANDARDS
- Questions MUST be directly related to the course content
- Avoid generic questions not specific to this course
- Ensure questions test understanding, not just memorization
- Make distractors (wrong answers) plausible and educational
- Include clear, helpful explanations for each correct answer

## COURSE-SPECIFIC EXAMPLES
{self._get_course_examples(course)}

## OUTPUT FORMAT
Generate exactly {num_questions} questions in this JSON format:

[
  {{
    "type": "multiple_choice",
    "content": "Specific question about course content",
    "options": ["Option A", "Option B", "Correct Option C", "Option D"],
    "correct_answer": 2,
    "explanation": "Clear explanation of why this is correct and why other options are wrong"
  }},
  {{
    "type": "true_false",
    "content": "Clear true/false statement about course content",
    "correct_answer": "True",
    "explanation": "Explanation supporting the true/false nature of the statement"
  }},
  {{
    "type": "short_answer",
    "content": "Question requiring a specific, concise answer",
    "correct_answer": "Precise answer",
    "explanation": "Context for the correct answer"
  }}
]

IMPORTANT: Return ONLY the JSON array. No markdown, no explanations, no additional text.
"""

        return prompt

    def _extract_course_context(self, course):
        """Extract and format comprehensive course information for context."""
        context_parts = []

        # Basic course information
        context_parts.append(f"Course Title: {getattr(course, 'title', 'General Course')}")
        context_parts.append(f"Course Code: {getattr(course, 'code', 'N/A')}")

        # Course description and summary
        description = getattr(course, 'summary', '') or getattr(course, 'description', '')
        if description:
            context_parts.append(f"Course Description: {description}")

        # Program information
        if hasattr(course, 'program') and course.program:
            context_parts.append(f"Program: {course.program.title}")
            if hasattr(course.program, 'summary') and course.program.summary:
                context_parts.append(f"Program Summary: {course.program.summary}")

        # Level and academic details
        level = getattr(course, 'level', '')
        year = getattr(course, 'year', '')
        semester = getattr(course, 'semester', '')
        credit = getattr(course, 'credit', 0)

        if level:
            context_parts.append(f"Academic Level: {level}")
        if year:
            context_parts.append(f"Year: {year}")
        if semester:
            context_parts.append(f"Semester: {semester}")
        if credit and credit > 0:
            context_parts.append(f"Credit Hours: {credit}")

        # Elective status
        is_elective = getattr(course, 'is_elective', False)
        context_parts.append(f"Course Type: {'Elective' if is_elective else 'Required'}")

        return '\n'.join(f"- {part}" for part in context_parts)

    def _get_difficulty_guidelines(self, difficulty):
        """Return detailed guidelines for each difficulty level."""
        guidelines = {
            'beginner': """
- Focus on basic concepts, definitions, and fundamental principles
- Questions should test recognition and basic understanding
- Use simple language and avoid complex terminology
- Expect direct answers from core course content""",

            'intermediate': """
- Focus on application, analysis, and problem-solving
- Questions should require understanding relationships between concepts
- Include practical scenarios and real-world applications
- Test ability to apply knowledge, not just memorize facts""",

            'advanced': """
- Focus on complex scenarios, critical thinking, and evaluation
- Questions should require synthesis of multiple concepts
- Include analysis of trade-offs, design decisions, and advanced applications
- Test deep understanding and ability to critique or extend concepts"""
        }
        return guidelines.get(difficulty.lower(), guidelines['intermediate'])

    def _get_question_type_specifications(self, question_types):
        """Return detailed specifications for each question type."""
        specs = []

        if 'multiple_choice' in question_types:
            specs.append("""For multiple_choice questions:
- Provide exactly 4 options (A, B, C, D)
- Only one correct answer, other options must be plausible but incorrect
- Options should be similar in length and format
- correct_answer should be the index (0, 1, 2, or 3) of the correct option
- Make distractors educational, not obviously wrong""")

        if 'true_false' in question_types:
            specs.append("""For true_false questions:
- Statement must be clearly either true or false based on course content
- Avoid ambiguous statements that could be interpreted differently
- correct_answer should be exactly "True" or "False" (case-sensitive)
- Statements should be specific factual claims""")

        if 'short_answer' in question_types:
            specs.append("""For short_answer questions:
- Require a specific, concise factual answer (1-3 words typically)
- Answer should be unambiguous and directly from course content
- Avoid questions that could have multiple valid answers
- Test specific knowledge rather than opinions""")

        return '\n\n'.join(specs)

    def _build_topic_focus(self, topics, course_context):
        """Build topic-specific focus instructions."""
        if not topics or topics.strip() == "":
            return "- Specific Topics: Focus on all core course content areas"

        # Clean and split topics
        topic_list = [t.strip() for t in topics.split(',') if t.strip()]
        if not topic_list:
            return "- Specific Topics: Focus on all core course content areas"

        topic_focus = f"- Specific Topics to emphasize: {', '.join(topic_list)}"
        topic_focus += "\n- Ensure questions specifically relate to these topics within the course context"

        return topic_focus

    def _get_course_examples(self, course):
        """Provide course-specific examples to guide the AI"""
        course_title = getattr(course, 'title', 'General Course')
        course_title_lower = course_title.lower()

        if 'python' in course_title_lower or 'programming' in course_title_lower:
            return """
- What is the output of print(2**3) in Python?
- How do you define a function in Python?
- What is the difference between list and tuple?
"""
        elif 'data science' in course_title_lower or 'data' in course_title_lower:
            return """
- What is the difference between supervised and unsupervised learning?
- How does linear regression work?
- What is the purpose of data preprocessing?
- How do you handle missing values in a dataset?
"""
        elif 'petroleum' in course_title_lower or 'oil' in course_title_lower:
            return """
- What is the process of oil refining?
- How does hydraulic fracturing work?
- What are the main components of crude oil?
- What is reservoir engineering?
"""
        elif 'computer engineering' in course_title_lower:
            return """
- What is the difference between Von Neumann and Harvard architecture?
- How does a CPU execute instructions?
- What are the main components of an operating system?
- How does memory hierarchy work?
"""
        elif 'mechanical engineering' in course_title_lower:
            return """
- What are Newton's laws of motion?
- How does a heat engine work?
- What is stress-strain relationship in materials?
- How do you calculate moment of inertia?
"""
        elif 'civil engineering' in course_title_lower:
            return """
- What are the different types of foundations?
- How do you calculate beam deflection?
- What is the purpose of reinforced concrete?
- How does structural analysis work?
"""
        elif 'electrical engineering' in course_title_lower:
            return """
- What is Ohm's law?
- How does an electric circuit work?
- What is electromagnetic induction?
- How do transformers work?
"""
        elif 'chemical engineering' in course_title_lower:
            return """
- What is mass balance in chemical processes?
- How does distillation work?
- What are the principles of chemical reactors?
- How do you calculate reaction rates?
"""
        elif 'database' in course_title_lower or 'sql' in course_title_lower:
            return """
- What is the purpose of SQL JOIN?
- What is database normalization?
- What is the difference between PRIMARY KEY and FOREIGN KEY?
"""
        elif 'web' in course_title_lower or 'django' in course_title_lower:
            return """
- What is the MVC pattern in web development?
- How does Django handle URL routing?
- What is the purpose of middleware?
"""
        elif 'math' in course_title_lower or 'calculus' in course_title_lower:
            return """
- What is the derivative of x²?
- How do you solve quadratic equations?
- What is the Pythagorean theorem?
"""
        elif 'statistics' in course_title_lower or 'probability' in course_title_lower:
            return """
- What is the difference between mean and median?
- How does hypothesis testing work?
- What is a normal distribution?
- How do you calculate confidence intervals?
"""
        elif 'physics' in course_title_lower:
            return """
- What is Newton's second law?
- How does wave interference work?
- What is the photoelectric effect?
- How do you calculate work and energy?
"""
        elif 'chemistry' in course_title_lower:
            return """
- What is the periodic table organization?
- How does acid-base titration work?
- What are chemical reaction types?
- How do you balance chemical equations?
"""
        else:
            return f"""
- Key concepts from {course_title}
- Important theories or principles
- Practical applications
- Historical context or developments
"""

    def _parse_response(self, response_text):
        try:
            # More robust cleaning
            cleaned_text = response_text.strip()

            # Remove all markdown code blocks
            if '```json' in cleaned_text:
                cleaned_text = cleaned_text.split('```json')[1]
            if '```' in cleaned_text:
                cleaned_text = cleaned_text.split('```')[0]

            # Remove any non-JSON prefixes/suffixes
            lines = cleaned_text.split('\n')
            json_lines = []
            in_json = False

            for line in lines:
                line = line.strip()
                if line.startswith('[') or line.startswith('{'):
                    in_json = True
                if in_json:
                    json_lines.append(line)
                if line.endswith(']') or line.endswith('}'):
                    break

            cleaned_text = '\n'.join(json_lines)
            cleaned_text = cleaned_text.strip()

            print(f"DEBUG: Cleaning response text: {cleaned_text}")  # Debug line

            questions = json.loads(cleaned_text)

            # Validate we got the right number of questions
            if len(questions) < 3:  # If we got too few questions
                print(f"DEBUG: Only got {len(questions)} questions, using fallback")
                return self._get_fallback_questions(10)

            # Validate question structure
            valid_questions = []
            for question in questions:
                if all(key in question for key in ['type', 'content', 'correct_answer', 'explanation']):
                    # Ensure multiple_choice questions have options
                    if question['type'] == 'multiple_choice' and 'options' in question:
                        valid_questions.append(question)
                    elif question['type'] in ['true_false', 'short_answer']:
                        valid_questions.append(question)

            print(f"DEBUG: Validated {len(valid_questions)} questions")  # Debug line
            return valid_questions

        except (json.JSONDecodeError, ValueError) as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response was: {response_text}")
            return self._get_fallback_questions(10)

    def _get_fallback_questions(self, num_questions):
        """Better fallback questions"""
        fallback_questions = [
            {
                "type": "multiple_choice",
                "content": "What is the main purpose of version control systems like Git?",
                "options": [
                    "To write documentation",
                    "To track changes in source code during development",
                    "To compile programs",
                    "To design user interfaces"
                ],
                "correct_answer": 1,
                "explanation": "Version control systems track changes in source code, allowing multiple developers to collaborate."
            },
            {
                "type": "true_false",
                "content": "Object-oriented programming focuses on procedures rather than objects.",
                "correct_answer": "False",
                "explanation": "Object-oriented programming focuses on objects that contain both data and methods, not just procedures."
            },
            {
                "type": "multiple_choice",
                "content": "Which data structure uses LIFO (Last-In-First-Out) principle?",
                "options": [
                    "Queue",
                    "Stack",
                    "Array",
                    "Linked List"
                ],
                "correct_answer": 1,
                "explanation": "Stack uses LIFO principle where the last element added is the first one to be removed."
            },
            {
                "type": "short_answer",
                "content": "What does API stand for in programming?",
                "correct_answer": "Application Programming Interface",
                "explanation": "API stands for Application Programming Interface, which defines how different software components should interact."
            },
            {
                "type": "true_false",
                "content": "Python uses static typing for variables.",
                "correct_answer": "False",
                "explanation": "Python uses dynamic typing, meaning variable types are determined at runtime rather than compile time."
            }
        ]
        return fallback_questions[:num_questions]
