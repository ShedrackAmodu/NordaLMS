from django import forms
from django.forms.widgets import RadioSelect, Textarea
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _
from django.forms.models import inlineformset_factory
from .models import Question, Quiz, MCQuestion, Choice,EssayQuestion



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
        exclude = []

    # Field for Multiple-Choice Questions (renamed to mc_questions)
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
        if self.instance.pk:
            self.fields["mc_questions"].initial = self.instance.question_set.instance_of(MCQuestion)
            self.fields["essay_questions"].initial = self.instance.question_set.instance_of(EssayQuestion)

    def save(self, commit=True):
        quiz = super(QuizAddForm, self).save(commit=False)
        if commit:
            quiz.save()
            # Combine the selected MC and Essay questions into the quiz's question set.
            all_questions = list(self.cleaned_data["mc_questions"]) + list(self.cleaned_data["essay_questions"])
            quiz.question_set.set(all_questions)
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


MCQuestionFormSet = inlineformset_factory(
    MCQuestion,
    Choice,
    form=MCQuestionForm,
    formset=MCQuestionFormSet,
    fields=["choice_text", "correct"],
    can_delete=True,
    extra=5,
)
