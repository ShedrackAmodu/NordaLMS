import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from accounts.decorators import lecturer_required
from .forms import (
    AIQuizConfigForm,
    EssayForm,
    MCQuestionForm,
    MCQuestionFormSet,
    QuestionForm,
    QuizAddForm,
)
from .models import (
    Course,
    EssayQuestion,
    GroqQuizConfig,
    GroqQuizSession,
    MCQuestion,
    Progress,
    Question,
    Quiz,
    Sitting,
)
from .gemini_quiz import GroqQuizGenerator


# ########################################################
# Quiz Views
# ########################################################


@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizCreateView(CreateView):
    model = Quiz
    form_class = QuizAddForm
    template_name = "quiz/quiz_form.html"

    def get_initial(self):
        initial = super().get_initial()
        course = get_object_or_404(Course, slug=self.kwargs["slug"])
        initial["course"] = course
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["course"] = get_object_or_404(Course, slug=self.kwargs["slug"])
        return context

    def form_valid(self, form):
        form.instance.course = get_object_or_404(Course, slug=self.kwargs["slug"])
        with transaction.atomic():
            self.object = form.save()
            return redirect(
                "mc_create", slug=self.kwargs["slug"], quiz_id=self.object.id
            )


@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizUpdateView(UpdateView):
    model = Quiz
    form_class = QuizAddForm
    template_name = "quiz/quiz_form.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Quiz, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["course"] = get_object_or_404(Course, slug=self.kwargs["slug"])
        return context

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            return redirect("quiz_index", self.kwargs["slug"])


@login_required
@lecturer_required
def quiz_delete(request, slug, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    quiz.delete()
    messages.success(request, "Quiz successfully deleted.")
    return redirect("quiz_index", slug=slug)


@login_required
def quiz_list(request, slug):
    course = get_object_or_404(Course, slug=slug)
    quizzes = Quiz.objects.filter(course=course).order_by("-timestamp")
    return render(
        request, "quiz/quiz_list.html", {"quizzes": quizzes, "course": course}
    )


# ########################################################
# Multiple Choice Question Views
# ########################################################


@method_decorator([login_required, lecturer_required], name="dispatch")
class MCQuestionCreate(CreateView):
    model = MCQuestion
    form_class = MCQuestionForm
    template_name = "quiz/mcquestion_form.html"

    # def get_form_kwargs(self):
    #     kwargs = super().get_form_kwargs()
    #     kwargs["quiz"] = get_object_or_404(Quiz, id=self.kwargs["quiz_id"])
    #     return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["course"] = get_object_or_404(Course, slug=self.kwargs["slug"])
        context["quiz_obj"] = get_object_or_404(Quiz, id=self.kwargs["quiz_id"])
        context["quiz_questions_count"] = Question.objects.filter(
            quiz=self.kwargs["quiz_id"]
        ).count()
        if self.request.method == "POST":
            context["formset"] = MCQuestionFormSet(self.request.POST)
        else:
            context["formset"] = MCQuestionFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]
        if formset.is_valid():
            with transaction.atomic():
                # Save the MCQuestion instance without committing to the database yet
                self.object = form.save(commit=False)
                self.object.save()

                # Retrieve the Quiz instance
                quiz = get_object_or_404(Quiz, id=self.kwargs["quiz_id"])

                # set the many-to-many relationship
                self.object.quiz.add(quiz)

                # Save the formset (choices for the question)
                formset.instance = self.object
                formset.save()

                if "another" in self.request.POST:
                    return redirect(
                        "mc_create",
                        slug=self.kwargs["slug"],
                        quiz_id=self.kwargs["quiz_id"],
                    )
                return redirect("quiz_index", slug=self.kwargs["slug"])
        else:
            return self.form_invalid(form)


# ########################################################
# Quiz Progress and Marking Views
# ########################################################


@method_decorator([login_required], name="dispatch")
class QuizUserProgressView(TemplateView):
    template_name = "quiz/progress.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        progress, _ = Progress.objects.get_or_create(user=self.request.user)
        context["cat_scores"] = progress.list_all_cat_scores
        context["exams"] = progress.show_exams()
        context["exams_counter"] = context["exams"].count()
        return context


@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizMarkingList(ListView):
    model = Sitting
    template_name = "quiz/quiz_marking_list.html"

    def get_queryset(self):
        queryset = Sitting.objects.filter(complete=True)
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                quiz__course__allocated_course__lecturer__pk=self.request.user.id
            )
        quiz_filter = self.request.GET.get("quiz_filter")
        if quiz_filter:
            queryset = queryset.filter(quiz__title__icontains=quiz_filter)
        user_filter = self.request.GET.get("user_filter")
        if user_filter:
            queryset = queryset.filter(user__username__icontains=user_filter)
        return queryset


@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizMarkingDetail(DetailView):
    model = Sitting
    template_name = "quiz/quiz_marking_detail.html"

    def post(self, request, *args, **kwargs):
        sitting = self.get_object()
        question_id = request.POST.get("qid")
        if question_id:
            question = Question.objects.get_subclass(id=int(question_id))
            if isinstance(question, EssayQuestion):
                score = request.POST.get("score")
                if score is not None:
                    progress = Progress.objects.get(user=sitting.user)
                    progress.update_score(question, int(score), 1)
            else:
                if int(question_id) in sitting.get_incorrect_questions:
                    sitting.remove_incorrect_question(question)
                else:
                    sitting.add_incorrect_question(question)

        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["questions"] = self.object.get_questions(with_answers=True)
        return context


# ########################################################
# Quiz Taking View
# ########################################################


@method_decorator([login_required], name="dispatch")
class QuizTake(FormView):
    form_class = QuestionForm
    template_name = "quiz/question.html"
    result_template_name = "quiz/result.html"

    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, slug=self.kwargs["slug"])
        self.course = get_object_or_404(Course, pk=self.kwargs["pk"])
        if not Question.objects.filter(quiz=self.quiz).exists():
            messages.warning(request, "This quiz has no questions available.")
            return redirect("quiz_index", slug=self.course.slug)

        self.sitting = Sitting.objects.user_sitting(
            request.user, self.quiz, self.course
        )
        if not self.sitting:
            messages.info(
                request,
                "You have already completed this quiz. Only one attempt is permitted.",
            )
            return redirect("quiz_index", slug=self.course.slug)

        # Set self.question and self.progress here
        self.question = self.sitting.get_first_question()
        self.progress = self.sitting.progress()

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["question"] = self.question
        return kwargs

    def get_form_class(self):
        if isinstance(self.question, EssayQuestion):
            return EssayForm
        return self.form_class

    def form_valid(self, form):
        self.form_valid_user(form)
        if not self.sitting.get_first_question():
            return self.final_result_user()
        return super().get(self.request)

    # Update the form_valid_user method in the QuizTake class
    def form_valid_user(self, form):
        progress, _ = Progress.objects.get_or_create(user=self.request.user)
        guess = form.cleaned_data["answers"]
        is_correct = False  # Default for essay questions

        if isinstance(self.question, EssayQuestion):
            # Essay questions: record answer but don't auto-score
            progress.update_score(self.question, 0, 1)  # 0 points initially
        else:
            # Handle MCQuestions normally
            is_correct = self.question.check_if_correct(guess)
            if is_correct:
                self.sitting.add_to_score(1)
                progress.update_score(self.question, 1, 1)
            else:
                self.sitting.add_incorrect_question(self.question)
                progress.update_score(self.question, 0, 1)

        # Handle previous question data
        if not self.quiz.answers_at_end:
            self.previous = {
                "previous_answer": guess,
                "previous_outcome": (
                    is_correct if not isinstance(self.question, EssayQuestion) else None
                ),
                "previous_question": self.question,
                "answers": (
                    self.question.get_choices()
                    if not isinstance(self.question, EssayQuestion)
                    else []
                ),
                "question_type": {self.question.__class__.__name__: True},
            }
        else:
            self.previous = {}

        # Store user response and remove the question from the queue
        self.sitting.add_user_answer(self.question, guess)
        self.sitting.remove_first_question()

        # Update for next question
        self.question = self.sitting.get_first_question()
        self.progress = self.sitting.progress()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["question"] = self.question
        context["quiz"] = self.quiz
        context["course"] = self.course
        if hasattr(self, "previous"):
            context["previous"] = self.previous
        if hasattr(self, "progress"):
            context["progress"] = self.progress
        return context

    def final_result_user(self):
        self.sitting.mark_quiz_complete()
        results = {
            "course": self.course,
            "quiz": self.quiz,
            "score": self.sitting.get_current_score,
            "max_score": self.sitting.get_max_score,
            "percent": self.sitting.get_percent_correct,
            "sitting": self.sitting,
            "previous": getattr(self, "previous", {}),
        }

        if self.quiz.answers_at_end:
            results["questions"] = self.sitting.get_questions(with_answers=True)
            results["incorrect_questions"] = self.sitting.get_incorrect_questions

        if (
            not self.quiz.exam_paper
            or self.request.user.is_superuser
            or self.request.user.is_lecturer
        ):
            self.sitting.delete()

        return render(self.request, self.result_template_name, results)


# ########################################################
# AI Quiz Views
# ########################################################

@method_decorator([login_required], name="dispatch")
class AIConfigView(CreateView):
    model = GroqQuizConfig
    form_class = AIQuizConfigForm
    template_name = "quiz/ai_quiz_config.html"

    def get_initial(self):
        initial = super().get_initial()
        # Set default course based on URL parameter or something
        return initial

    def get_queryset(self):
        return GroqQuizConfig.objects.filter(user=self.request.user)

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        from django.urls import reverse
        return reverse('ai_quiz_start', kwargs={'pk': self.object.pk})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # For lecturers, only show courses they are allocated to
        if self.request.user.is_lecturer and not self.request.user.is_superuser:
            form.fields['course'].queryset = Course.objects.filter(
                allocated_course__lecturer=self.request.user
            )
        # Students and superusers can see all courses
        return form


from .decorators import handle_ai_errors

@login_required
@handle_ai_errors
def ai_quiz_start(request, pk):
    config = get_object_or_404(GroqQuizConfig, pk=pk, user=request.user)

    # Validate configuration before proceeding
    if not settings.GROQ_API_KEY:
        messages.error(request, "AI quiz service is currently unavailable.")
        return redirect('ai_quiz_config')

    try:
        # Generate questions using Groq
        generator = GroqQuizGenerator()

        # Ensure question_types is properly formatted
        question_types = config.question_types
        if isinstance(question_types, str):
            question_types = [question_types]

        logger.info(f"Starting AI quiz generation for user {request.user.username}")

        questions = generator.generate_questions(
            course=config.course,
            difficulty=config.difficulty,
            num_questions=config.num_questions,
            question_types=question_types,
            topics=config.topics
        )

        if not questions:
            messages.warning(request, "No questions could be generated. Using fallback questions.")
            questions = generator._get_fallback_questions(config.num_questions)

        # Create quiz session
        questions_per_session = config.questions_per_session
        session_questions = questions[:questions_per_session]

        session = GroqQuizSession.objects.create(
            user=request.user,
            course=config.course,
            config=config,
            questions=questions,
            session_questions=session_questions,
        )

        messages.success(request, f"AI quiz generated with {len(session.questions)} questions!")
        return redirect('ai_quiz_take', session_id=session.id)

    except Exception as e:
        logger.error(f"Quiz generation failed: {str(e)}")
        messages.error(request, f"Failed to start quiz: {str(e)}")
        return redirect('ai_quiz_config')


@login_required
@handle_ai_errors
def ai_quiz_status(request):
    """Check if AI quiz service is properly configured"""
    status = {
        'groq_configured': bool(settings.GROQ_API_KEY),
        'api_key_length': len(settings.GROQ_API_KEY) if settings.GROQ_API_KEY else 0,
        'model': getattr(settings, 'GROQ_MODELS', {}).get('quiz_generation', 'llama3-70b-8192')
    }

    # Test API connection
    if status['groq_configured']:
        try:
            generator = GroqQuizGenerator()
            test_response = generator.client.chat.completions.create(
                model=status['model'],
                messages=[{"role": "user", "content": "Say 'OK'"}],
                max_tokens=5
            )
            status['api_working'] = True
            status['api_test'] = "Success"
        except Exception as e:
            status['api_working'] = False
            status['api_test'] = str(e)

    return render(request, 'quiz/ai_quiz_status.html', {'status': status})


@method_decorator([login_required], name="dispatch")
class AIQuizTakeView(TemplateView):
    template_name = "quiz/ai_quiz_take.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_id = self.kwargs['session_id']
        session = get_object_or_404(GroqQuizSession, id=session_id, user=self.request.user)

        current_question = session.get_current_question()
        progress_info = session.get_session_progress()

        context.update({
            'session': session,
            'question': current_question,
            'session_progress': progress_info['session_progress'],
            'total_progress': progress_info['total_progress'],
            'question_number': session.current_question_index + 1,
            'total_questions_in_session': len(session.session_questions),
            'total_questions_overall': progress_info['total_questions'],
            'can_continue': session.can_continue_to_next_session(),
            'questions_per_session': session.config.questions_per_session,
        })
        return context


@login_required
def ai_quiz_submit(request, session_id):
    if request.method == 'POST':
        session = get_object_or_404(GroqQuizSession, id=session_id, user=request.user)
        answer = request.POST.get('answer')
        continue_quiz = request.POST.get('continue_quiz')

        if answer is not None:
            is_correct = session.submit_answer(answer)

            # Check if current session is complete
            if session.current_question_index >= len(session.session_questions):
                # If there are more questions and user wants to continue
                if session.can_continue_to_next_session() and continue_quiz:
                    session.start_next_session()
                    messages.info(request, f"Session {session.session_number} complete! Starting session {session.session_number + 1}")
                    return redirect('ai_quiz_take', session_id=session_id)
                # If there are no more questions or user doesn't want to continue
                else:
                    session.completed = True
                    from django.utils.timezone import now
                    session.completed_at = now()
                    session.save()
                    return redirect('ai_quiz_result', session_id=session_id)

            return redirect('ai_quiz_take', session_id=session_id)

    return redirect('ai_quiz_take', session_id=session_id)


@login_required
def ai_quiz_continue(request, session_id):
    """Continue to the next session if available"""
    session = get_object_or_404(GroqQuizSession, id=session_id, user=request.user)

    if session.can_continue_to_next_session():
        session.start_next_session()
        messages.info(request, f"Continuing to session {session.session_number} of questions.")
    else:
        messages.warning(request, "No more questions available.")

    return redirect('ai_quiz_take', session_id=session_id)


@method_decorator([login_required], name="dispatch")
class AIQuizResultView(DetailView):
    model = GroqQuizSession
    template_name = "quiz/ai_quiz_result.html"
    context_object_name = 'session'
    pk_url_kwarg = 'session_id'

    def get_queryset(self):
        return GroqQuizSession.objects.filter(user=self.request.user)


@login_required
def ai_quiz_history(request):
    sessions = GroqQuizSession.objects.filter(user=request.user, completed=True).order_by('-completed_at')
    return render(request, 'quiz/ai_quiz_history.html', {'sessions': sessions})
