from django.urls import path
from . import views

urlpatterns = [
    path("<slug>/quizzes/", views.quiz_list, name="quiz_index"),
    path("progress/", views.QuizUserProgressView.as_view(), name="quiz_progress"),
    path("marking_list/", views.QuizMarkingList.as_view(), name="quiz_marking"),
    path("marking/<int:pk>/", views.QuizMarkingDetail.as_view(), name="quiz_marking_detail"),
    path("<int:pk>/<slug>/take/", views.QuizTake.as_view(), name="quiz_take"),
    path("<slug>/quiz_add/", views.QuizCreateView.as_view(), name="quiz_create"),
    path("<slug>/<int:pk>/add/", views.QuizUpdateView.as_view(), name="quiz_update"),
    path("<slug>/<int:pk>/delete/", views.quiz_delete, name="quiz_delete"),
    path("mc-question/add/<slug>/<int:quiz_id>/", views.MCQuestionCreate.as_view(), name="mc_create"),
    path("mc-question/add/<int:pk>/<int:quiz_pk>/", views.MCQuestionCreate.as_view(), name="mc_create"),
    path("sitting/start/<slug>/<int:pk>/", views.QuizTake.as_view(), name="quiz_sitting_start"),
    path("sitting/result/<slug>/<int:pk>/", views.QuizTake.as_view(), name="quiz_sitting_result"),

    # AI Quiz URLs
    path("ai-quiz/config/", views.AIConfigView.as_view(), name="ai_quiz_config"),
    path("ai-quiz/start/<int:pk>/", views.ai_quiz_start, name="ai_quiz_start"),
    path("ai-quiz/status/", views.ai_quiz_status, name="ai_quiz_status"),
    path("ai-quiz/take/<int:session_id>/", views.AIQuizTakeView.as_view(), name="ai_quiz_take"),
    path("ai-quiz/submit/<int:session_id>/", views.ai_quiz_submit, name="ai_quiz_submit"),
    path("ai-quiz/continue/<int:session_id>/", views.ai_quiz_continue, name="ai_quiz_continue"),
    path("ai-quiz/result/<int:session_id>/", views.AIQuizResultView.as_view(), name="ai_quiz_result"),
    path("ai-quiz/history/", views.ai_quiz_history, name="ai_quiz_history"),
]
