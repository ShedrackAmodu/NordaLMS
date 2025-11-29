from django import forms
from django.forms.widgets import RadioSelect, Textarea
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _
from django.forms.models import inlineformset_factory
from .models import Question, Quiz, MCQuestion, Choice, EssayQuestion, GroqQuizConfig



class QuestionForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        if isinstance(question, EssayQuestion):
            self.fields["answers"] = forms.CharField(
                widget=Textarea(attrs={"style": "width:100%"})
            )
        else:
            choice_list = [x for x in question.get_choices_list()]
            self.fields["answers"] = forms.ChoiceField(
                choices=choice_list, widget=RadioSelect
            )
        


class EssayForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(EssayForm, self).__init__(*args, **kwargs)
        self.fields["answers"] = forms.CharField(
            widget=Textarea(attrs={"style": "width:100%"})
        )


class QuizAddForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'category', 'description', 'random_order',
                 'answers_at_end', 'exam_paper', 'single_attempt',
                 'pass_mark', 'draft']
        # Remove course from fields since it's set automatically

    # Field for Multiple-Choice Questions
    mc_questions = forms.ModelMultipleChoiceField(
        queryset=MCQuestion.objects.all(),
        required=False,
        label=_("Multiple-Choice Questions"),
        widget=FilteredSelectMultiple(verbose_name=_("MC Questions"), is_stacked=False),
    )

    # Field for Essay Questions
    essay_questions = forms.ModelMultipleChoiceField(
        queryset=EssayQuestion.objects.all(),
        required=False,
        label=_("Essay Questions"),
        widget=FilteredSelectMultiple(verbose_name=_("Essay Questions"), is_stacked=False),
    )

    def __init__(self, *args, **kwargs):
        super(QuizAddForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Get MCQuestions associated with this quiz
            mc_questions = self.instance.question_set.instance_of(MCQuestion)
            self.fields["mc_questions"].initial = mc_questions

            # Get EssayQuestions associated with this quiz
            essay_questions = self.instance.question_set.instance_of(EssayQuestion)
            self.fields["essay_questions"].initial = essay_questions

    def save(self, commit=True):
        quiz = super(QuizAddForm, self).save(commit=False)
        if commit:
            quiz.save()
            # Clear existing questions and add new selections
            quiz.question_set.clear()

            # Add MC questions
            for question in self.cleaned_data["mc_questions"]:
                quiz.question_set.add(question)

            # Add Essay questions
            for question in self.cleaned_data["essay_questions"]:
                quiz.question_set.add(question)

            self.save_m2m()
        return quiz



class MCQuestionForm(forms.ModelForm):
    class Meta:
        model = MCQuestion
        exclude = ()


class MCQuestionFormSet(forms.BaseInlineFormSet):
    def clean(self):
        """
        Custom validation for the formset to ensure:
        1. At least two choices are provided and not marked for deletion.
        2. At least one of the choices is marked as correct.
        """
        super().clean()

        # Collect non-deleted forms
        valid_forms = [
            form for form in self.forms if not form.cleaned_data.get("DELETE", True)
        ]

        valid_choices = [
            "choice_text" in form.cleaned_data.keys() for form in valid_forms
        ]
        if not all(valid_choices):
            raise forms.ValidationError("You must add a valid choice name.")

        # If all forms are deleted, raise a validation error
        if len(valid_forms) < 2:
            raise forms.ValidationError("You must provide at least two choices.")

        # Check if at least one of the valid forms is marked as correct
        correct_choices = [
            form.cleaned_data.get("correct", False) for form in valid_forms
        ]

        if not any(correct_choices):
            raise forms.ValidationError("One choice must be marked as correct.")

        if correct_choices.count(True) > 1:
            raise forms.ValidationError("Only one choice must be marked as correct.")


class AIQuizConfigForm(forms.ModelForm):
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice (4 options each)'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer (1-3 words)'),
    ]

    question_types = forms.MultipleChoiceField(
        choices=QUESTION_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        initial=['multiple_choice'],  # Default selection
        label="Question Types",
        help_text="Select the types of questions you want in your quiz. Multiple choice tests recognition, true/false tests basic facts, short answer tests specific knowledge."
    )

    class Meta:
        model = GroqQuizConfig
        fields = ['course', 'difficulty', 'num_questions', 'questions_per_session', 'question_types', 'topics']
        widgets = {
            'topics': forms.Textarea(attrs={
                'placeholder': 'Optional: Specify topics to focus on (e.g., functions, loops, databases). Leave empty for general course content.',
                'rows': 3,
                'class': 'form-control'
            }),
            'num_questions': forms.NumberInput(attrs={
                'min': '1',
                'max': '20',
                'class': 'form-control'
            }),
            'questions_per_session': forms.NumberInput(attrs={
                'min': '1',
                'max': '20',
                'class': 'form-control'
            }),
        }
        help_texts = {
            'difficulty': 'Beginner: Basic concepts | Intermediate: Application & analysis | Advanced: Critical thinking',
            'num_questions': 'Maximum 20 questions. AI will balance question types based on your selection above.',
            'questions_per_session': 'How many questions to show at once? Can continue to next batch after completing each session.',
            'course': 'Questions will be generated based on this course\'s title, description, and academic level.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set initial question types from instance
        if self.instance and self.instance.pk and self.instance.question_types:
            self.fields['question_types'].initial = self.instance.question_types

        # Add helpful styling
        self.fields['difficulty'].widget.attrs.update({'class': 'form-control'})
        self.fields['course'].widget.attrs.update({'class': 'form-control'})

    def clean_num_questions(self):
        num_questions = self.cleaned_data.get('num_questions')
        if num_questions < 1:
            raise forms.ValidationError("Number of questions must be at least 1")
        if num_questions > 20:
            raise forms.ValidationError("Number of questions cannot exceed 20 for optimal quiz quality")
        return num_questions

    def clean_question_types(self):
        question_types = self.cleaned_data.get('question_types')
        if not question_types:
            raise forms.ValidationError("Please select at least one question type to generate meaningful quiz questions")
        return question_types

    def clean_questions_per_session(self):
        questions_per_session = self.cleaned_data.get('questions_per_session')
        num_questions = self.cleaned_data.get('num_questions')

        if questions_per_session < 1:
            raise forms.ValidationError("Questions per session must be at least 1")
        if num_questions and questions_per_session > num_questions:
            raise forms.ValidationError("Questions per session cannot exceed total number of questions")
        return questions_per_session

    def clean_topics(self):
        topics = self.cleaned_data.get('topics', '').strip()
        if topics:
            # Validate comma-separated format and clean up
            topic_list = [t.strip() for t in topics.split(',') if t.strip()]
            if len(topic_list) > 10:
                raise forms.ValidationError("Please limit to 10 topics maximum for focused quiz generation")
            return ', '.join(topic_list)
        return topics

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.question_types = self.cleaned_data['question_types']
        if commit:
            instance.save()
        return instance


MCQuestionFormSet = inlineformset_factory(
    MCQuestion,
    Choice,
    form=MCQuestionForm,
    formset=MCQuestionFormSet,
    fields=["choice_text", "correct"],
    can_delete=True,
    extra=5,
)
