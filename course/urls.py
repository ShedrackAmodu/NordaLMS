from django.urls import path
from . import views


urlpatterns = [
    # Program urls
    path("", views.ProgramFilterView.as_view(), name="programs"),
    path("<int:pk>/detail/", views.program_detail, name="program_detail"),
    path("add/", views.program_add, name="add_program"),
    path("<int:pk>/edit/", views.program_edit, name="edit_program"),
    path("<int:pk>/delete/", views.program_delete, name="program_delete"),
    # Course urls
    path("course/<slug>/detail/", views.course_single, name="course_detail"),
    path("<int:pk>/course/add/", views.course_add, name="course_add"),
    path("course/<slug>/edit/", views.course_edit, name="edit_course"),
    path("course/delete/<slug>/", views.course_delete, name="delete_course"),
    # Course Admin Panel
    path("course/list/", views.course_list_view, name="course_list"),
    path("course/admin/add/", views.course_add_admin, name="course_add_admin"),
    path("course/admin/<slug>/edit/", views.course_edit_admin, name="course_edit_admin"),
    path("course/admin/<slug>/delete/", views.course_delete_admin, name="course_delete_admin"),
    path("course/admin/<slug>/history/", views.course_history, name="course_history"),
    # CourseAllocation urls
    path(
        "course/assign/",
        views.CourseAllocationFormView.as_view(),
        name="course_allocation",
    ),
    path(
        "course/allocated/",
        views.CourseAllocationFilterView.as_view(),
        name="course_allocation_view",
    ),
    path(
        "allocated_course/<int:pk>/edit/",
        views.edit_allocated_course,
        name="edit_allocated_course",
    ),
    path(
        "course/<int:pk>/deallocate/", views.deallocate_course, name="course_deallocate"
    ),
    # File uploads urls
    path(
        "course/<slug>/documentations/upload/",
        views.handle_file_upload,
        name="upload_file_view",
    ),
    path(
        "course/<slug>/documentations/<int:file_id>/edit/",
        views.handle_file_edit,
        name="upload_file_edit",
    ),
    path(
        "course/<slug>/documentations/<int:file_id>/delete/",
        views.handle_file_delete,
        name="upload_file_delete",
    ),
    # Video uploads urls
    path(
        "course/<slug>/video_tutorials/upload/",
        views.handle_video_upload,
        name="upload_video",
    ),
    path(
        "course/<slug>/video_tutorials/<video_slug>/detail/",
        views.handle_video_single,
        name="video_single",
    ),
    path(
        "course/<slug>/video_tutorials/<video_slug>/edit/",
        views.handle_video_edit,
        name="upload_video_edit",
    ),
    path(
        "course/<slug>/video_tutorials/<video_slug>/delete/",
        views.handle_video_delete,
        name="upload_video_delete",
    ),
    # course registration
    path("course/registration/", views.course_registration, name="course_registration"),
    path("course/drop/", views.course_drop, name="course_drop"),
    path("department/add_drop/", views.department_add_drop, name="department_add_drop"),
    path("my_courses/", views.user_course_list, name="user_course_list"),
    path("<slug:slug>/discussion/", views.discussion_list, name="discussion_list"),
    path("discussion/<int:discussion_id>/comment/", views.add_comment, name="add_comment"),
    path('comment/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('discussion/<int:discussion_id>/delete/', views.delete_discussion, name='delete_discussion'),
    path("live-class/new/<slug:slug>/", views.create_live_class, name="create_live_class"),
    path("live-class/<int:pk>/",views.live_class_detail, name="live_class_detail"),
    path("courses/<slug:slug>/live-class/create/",views.create_live_class, name="create_live_class"),
]
