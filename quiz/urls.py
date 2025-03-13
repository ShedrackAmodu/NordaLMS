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
]
