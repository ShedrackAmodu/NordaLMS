import calendar
import datetime
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count

from accounts.decorators import admin_required, lecturer_required
from accounts.models import User, Student
from course.models import Course, Upload, UploadVideo
from result.models import TakenCourse
from .forms import SessionForm, SemesterForm, NewsAndEventsForm
from .models import NewsAndEvents, ActivityLog, Session, Semester
from .utils import get_school_calendar, get_school_calendar_with_navigation


# ########################################################
# News & Events
# ########################################################


def guest_view(request):
    return render(request, "guest/guest.html")  # Ensure 'guest.html' exists


def home_view(request):
    if request.user.is_authenticated:
        # Get year and month from request or use current date
        year = request.GET.get('year')
        month = request.GET.get('month')

        if year and month:
            try:
                year = int(year)
                month = int(month)
            except (ValueError, TypeError):
                year = datetime.date.today().year
                month = datetime.date.today().month
        else:
            today = datetime.date.today()
            year = today.year
            month = today.month

        # Get calendar with navigation data
        calendar_data = get_school_calendar_with_navigation(year, month)

        items = NewsAndEvents.objects.all().order_by("-updated_date")

        context = {
            "title": "News & Events",
            "items": items,
            "calendar_html": calendar_data['calendar_html'],
            "current_year": calendar_data['current_year'],
            "current_month": calendar_data['current_month'],
            "prev_year": calendar_data['prev_year'],
            "prev_month": calendar_data['prev_month'],
            "next_year": calendar_data['next_year'],
            "next_month": calendar_data['next_month'],
            "month_name": calendar_data['month_name'],
            "events_count": calendar_data['events_count'],
            "today_year": datetime.date.today().year,
            "today_month": datetime.date.today().month,
            "month_list": [(i, calendar.month_name[i]) for i in range(1, 13)],
            "year_range": range(datetime.date.today().year - 5, datetime.date.today().year + 6),
        }
        template = "core/index.html"
    else:
        context = {}
        template = "guest/guest.html"
    return render(request, template, context)


@login_required
def calendar_view(request, year=None, month=None):
    """AJAX view for calendar navigation"""
    if request.method == "GET" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        today = datetime.date.today()
        try:
            year = int(year) if year else today.year
            month = int(month) if month else today.month
            # Validate month range
            if month < 1 or month > 12:
                raise ValueError("Invalid month")
        except (ValueError, TypeError):
            year, month = today.year, today.month

        calendar_html = get_school_calendar(year, month)
        from django.http import JsonResponse
        return JsonResponse({'calendar_html': calendar_html})
    else:
        from django.http import JsonResponse
        return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def calendar_day_events(request, year, month, day):
    """View to show events for a specific day (AJAX only)"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        events = NewsAndEvents.objects.filter(
            event_date__year=year,
            event_date__month=month,
            event_date__day=day
        ).exclude(event_date__isnull=True)

        context = {
            'events': events,
            'date': datetime.date(year, month, day),
            'year': year,
            'month': month,
            'day': day,
        }
        return render(request, 'core/calendar_day_events.html', context)
    else:
        from django.http import JsonResponse
        return JsonResponse({'error': 'AJAX request required'}, status=400)


@login_required
@admin_required
def dashboard_view(request):
    logs = ActivityLog.objects.all().order_by("-created_at")[:10]
    gender_count = Student.get_gender_count()

    # Overall attendance
    attendance_avg = TakenCourse.objects.aggregate(avg_attendance=Avg('attendance'))['avg_attendance'] or 0

    # Student levels
    student_levels = list(Student.objects.values('level').annotate(count=Count('level')).order_by('level'))

    # Average grade per course (using GPA points)
    course_grades = list(TakenCourse.objects.values('course__title').annotate(avg_grade=Avg('point')).order_by('course__title'))
    # Convert Decimal to float for JSON serialization
    for item in course_grades:
        item['avg_grade'] = float(item['avg_grade'])

    # Overall Course Resources
    total_videos = UploadVideo.objects.count()
    total_docs = Upload.objects.count()
    total_courses = Course.objects.count()

    # Enrollments per course
    enrollments_per_course = list(TakenCourse.objects.values('course__title').annotate(enrollments=Count('student')).order_by('course__title'))

    # Website traffic approximation (last 6 months ActivityLog counts)
    today = datetime.date.today()
    traffic_labels = []
    traffic_counts = []
    for i in range(5, -1, -1):  # last 6 months
        month_start = today.replace(day=1) - datetime.timedelta(days=30*(5-i))
        month_end = (month_start + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
        count = ActivityLog.objects.filter(created_at__date__gte=month_start, created_at__date__lte=month_end).count()
        traffic_labels.append(month_start.strftime('%b %Y'))
        traffic_counts.append(count)

    # Upcoming events
    upcoming_events = NewsAndEvents.objects.filter(posted_as='Event', event_date__gte=today).order_by('event_date')[:5]

    context = {
        "student_count": User.objects.get_student_count(),
        "lecturer_count": User.objects.get_lecturer_count(),
        "superuser_count": User.objects.get_superuser_count(),
        "males_count": gender_count["M"],
        "females_count": gender_count["F"],
        "attendance_avg": round(attendance_avg, 2),
        "student_levels": json.dumps(student_levels),
        "course_grades": json.dumps(course_grades),
        "total_videos": total_videos,
        "total_docs": total_docs,
        "total_courses": total_courses,
        "enrollments_per_course": json.dumps(enrollments_per_course),
        "traffic_labels": json.dumps(traffic_labels),
        "traffic_counts": json.dumps(traffic_counts),
        "upcoming_events": upcoming_events,
        "logs": logs,
    }
    return render(request, "core/dashboard.html", context)


@login_required
@admin_required
def post_add(request):
    if request.method == "POST":
        form = NewsAndEventsForm(request.POST)
        title = form.cleaned_data.get("title", "Post") if form.is_valid() else None
        if form.is_valid():
            form.save()
            messages.success(request, f"{title} has been uploaded.")
            return redirect("home")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = NewsAndEventsForm()
    return render(request, "core/post_add.html", {"title": "Add Post", "form": form})


@login_required
@admin_required
def edit_post(request, pk):
    instance = get_object_or_404(NewsAndEvents, pk=pk)
    if request.method == "POST":
        form = NewsAndEventsForm(request.POST, instance=instance)
        title = form.cleaned_data.get("title", "Post") if form.is_valid() else None
        if form.is_valid():
            form.save()
            messages.success(request, f"{title} has been updated.")
            return redirect("home")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = NewsAndEventsForm(instance=instance)
    return render(request, "core/post_add.html", {"title": "Edit Post", "form": form})


@login_required
@admin_required
def delete_post(request, pk):
    post = get_object_or_404(NewsAndEvents, pk=pk)
    post_title = post.title
    post.delete()
    messages.success(request, f"{post_title} has been deleted.")
    return redirect("home")


# ########################################################
# Session
# ########################################################
@login_required
@lecturer_required
def session_list_view(request):
    """Show list of all sessions"""
    sessions = Session.objects.all().order_by("-is_current_session", "-session")
    return render(request, "core/session_list.html", {"sessions": sessions})


@login_required
@lecturer_required
def session_add_view(request):
    """Add a new session"""
    if request.method == "POST":
        form = SessionForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get("is_current_session"):
                unset_current_session()
            form.save()
            messages.success(request, "Session added successfully.")
            return redirect("session_list")
    else:
        form = SessionForm()
    return render(request, "core/session_update.html", {"form": form})


@login_required
@lecturer_required
def session_update_view(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if request.method == "POST":
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            if form.cleaned_data.get("is_current_session"):
                unset_current_session()
            form.save()
            messages.success(request, "Session updated successfully.")
            return redirect("session_list")
    else:
        form = SessionForm(instance=session)
    return render(request, "core/session_update.html", {"form": form})


@login_required
@lecturer_required
def session_delete_view(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if session.is_current_session:
        messages.error(request, "You cannot delete the current session.")
    else:
        session.delete()
        messages.success(request, "Session successfully deleted.")
    return redirect("session_list")


def unset_current_session():
    """Unset current session"""
    current_session = Session.objects.filter(is_current_session=True).first()
    if current_session:
        current_session.is_current_session = False
        current_session.save()


# ########################################################
# Semester
# ########################################################
@login_required
@lecturer_required
def semester_list_view(request):
    semesters = Semester.objects.all().order_by("-is_current_semester", "-semester")
    return render(request, "core/semester_list.html", {"semesters": semesters})


@login_required
@lecturer_required
def semester_add_view(request):
    if request.method == "POST":
        form = SemesterForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get("is_current_semester"):
                unset_current_semester()
                unset_current_session()
            form.save()
            messages.success(request, "Semester added successfully.")
            return redirect("semester_list")
    else:
        form = SemesterForm()
    return render(request, "core/semester_update.html", {"form": form})


@login_required
@lecturer_required
def semester_update_view(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if request.method == "POST":
        form = SemesterForm(request.POST, instance=semester)
        if form.is_valid():
            if form.cleaned_data.get("is_current_semester"):
                unset_current_semester()
                unset_current_session()
            form.save()
            messages.success(request, "Semester updated successfully!")
            return redirect("semester_list")
    else:
        form = SemesterForm(instance=semester)
    return render(request, "core/semester_update.html", {"form": form})


@login_required
@lecturer_required
def semester_delete_view(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if semester.is_current_semester:
        messages.error(request, "You cannot delete the current semester.")
    else:
        semester.delete()
        messages.success(request, "Semester successfully deleted.")
    return redirect("semester_list")


def unset_current_semester():
    """Unset current semester"""
    current_semester = Semester.objects.filter(is_current_semester=True).first()
    if current_semester:
        current_semester.is_current_semester = False
        current_semester.save()


# ########################################################
# Page Views
# ########################################################

def pricing_view(request):
    return render(request, "guest/pricing.html")


def about_view(request):
    return render(request, "guest/about.html")


def contact_view(request):
    return render(request, "guest/contact.html")


def documentation_view(request):
    return render(request, "guest/resources/documentation.html")


# ########################################################
# Feature Views
# ########################################################

def student_features_view(request):
    return render(request, "guest/features/student.html")


def lecturer_features_view(request):
    return render(request, "guest/features/lecturer.html")


def parent_features_view(request):
    return render(request, "guest/features/parent.html")


def admin_features_view(request):
    return render(request, "guest/features/admin.html")


# ########################################################
# Resources Views
# ########################################################

def blog_view(request):
    return render(request, "guest/resources/blog.html")

def support_view(request):
    return render(request, "guest/resources/support.html")

def api_view(request):
    return render(request, "guest/resources/api.html")


# ########################################################
# Legal Views
# ########################################################

def privacy_view(request):
    return render(request, "guest/legal/privacy.html")

def terms_view(request):
    return render(request, "guest/legal/terms.html")

def cookies_view(request):
    return render(request, "guest/legal/cookies.html")

def gdpr_view(request):
    return render(request, "guest/legal/gdpr.html")
