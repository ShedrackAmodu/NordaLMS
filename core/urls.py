from django.urls import path
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views


from .views import (
    home_view,
    calendar_view,
    calendar_day_events,
    post_add,
    edit_post,
    delete_post,
    session_list_view,
    session_add_view,
    session_update_view,
    session_delete_view,
    semester_list_view,
    semester_add_view,
    semester_update_view,
    semester_delete_view,
    dashboard_view,
    guest_view,
    pricing_view,
    about_view,
    contact_view,
    documentation_view,
    student_features_view,
    lecturer_features_view,
    parent_features_view,
    admin_features_view,
    blog_view,
    support_view,
    api_view,
    privacy_view,
    terms_view,
    cookies_view,
    gdpr_view,
)
from django.views.generic import TemplateView

urlpatterns = [
    # Accounts url
    path("", home_view, name="home"),
    path("calendar/<int:year>/<int:month>/", calendar_view, name="calendar_ajax"),
    path('calendar/<int:year>/<int:month>/<int:day>/', calendar_day_events, name='calendar_day_events'),
    path("add_item/", post_add, name="add_item"),
    path("item/<int:pk>/edit/", edit_post, name="edit_post"),
    path("item/<int:pk>/delete/", delete_post, name="delete_post"),
    path("session/", session_list_view, name="session_list"),
    path("session/add/", session_add_view, name="add_session"),
    path("session/<int:pk>/edit/", session_update_view, name="edit_session"),
    path("session/<int:pk>/delete/", session_delete_view, name="delete_session"),
    path("semester/", semester_list_view, name="semester_list"),
    path("semester/add/", semester_add_view, name="add_semester"),
    path("semester/<int:pk>/edit/", semester_update_view, name="edit_semester"),
    path("semester/<int:pk>/delete/", semester_delete_view, name="delete_semester"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("accounts/logout/", LogoutView.as_view(next_page="guest"), name="logout"),
    path("guest/", TemplateView.as_view(template_name="guest/guest.html"), name="guest"),

    # Page URLs
    path("pricing/", pricing_view, name="pricing"),
    path("about/", about_view, name="about"),
    path("contact/", contact_view, name="contact"),
    path("resources/documentation/", documentation_view, name="documentation"),

    # Feature URLs
    path("features/student/", student_features_view, name="student_features"),
    path("features/lecturer/", lecturer_features_view, name="lecturer_features"),
    path("features/parent/", parent_features_view, name="parent_features"),
    path("features/admin/", admin_features_view, name="admin_features"),

    # Resources URLs
    path("resources/blog/", blog_view, name="blog"),
    path("resources/support/", support_view, name="support"),
    path("resources/api/", api_view, name="api"),

    # Legal URLs
    path("privacy/", privacy_view, name="privacy"),
    path("terms/", terms_view, name="terms"),
    path("cookies/", cookies_view, name="cookies"),
    path("gdpr/", gdpr_view, name="gdpr"),
]
