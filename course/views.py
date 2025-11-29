from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django_filters.views import FilterView
from django.views.generic import ListView

from accounts.decorators import admin_required, lecturer_required, student_required, dep_head_required
from accounts.models import Student, DepartmentHead
from core.models import Semester
from course.filters import CourseAllocationFilter, CourseFilter, ProgramFilter
from course.forms import (
    CourseAddForm,
    CourseAllocationForm,
    EditCourseAllocationForm,
    ProgramForm,
    UploadFormFile,
    UploadFormVideo,
    DiscussionForm,
    CommentEditForm,
    CommentForm,
    CourseOfferForm,
)
from course.models import (
    Course,
    CourseAllocation,
    Program,
    Upload,
    UploadVideo,
    Discussion,
    Comment,
    CourseOffer,
    LiveClass,
)
from result.models import TakenCourse
from course.decorators import is_calender_on


# ########################################################
# Program Views
# ########################################################


@method_decorator([login_required, lecturer_required], name="dispatch")
class ProgramFilterView(FilterView):
    filterset_class = ProgramFilter
    template_name = "course/program_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Programs"
        return context


@login_required
@lecturer_required
def program_add(request):
    if request.method == "POST":
        form = ProgramForm(request.POST)
        if form.is_valid():
            program = form.save()
            messages.success(request, f"Program '{program.title}' has been created.")
            return redirect("programs")
        messages.error(request, "Please correct the errors below.")
    else:
        form = ProgramForm()

    return render(
        request, "course/program_add.html", {"title": "Add Program", "form": form}
    )


@login_required
def program_detail(request, pk):
    program = get_object_or_404(Program, pk=pk)
    courses = Course.objects.filter(program_id=pk).order_by("-year")
    credits = courses.aggregate(total_credits=Sum("credit"))

    paginator = Paginator(courses, 10)
    page = request.GET.get("page")
    courses = paginator.get_page(page)

    return render(
        request,
        "course/program_single.html",
        {
            "title": program.title,
            "program": program,
            "courses": courses,
            "credits": credits,
        },
    )


@login_required
@lecturer_required
def program_edit(request, pk):
    program = get_object_or_404(Program, pk=pk)

    if request.method == "POST":
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            program = form.save()
            messages.success(request, f"Program '{program.title}' has been updated.")
            return redirect("programs")
        messages.error(request, "Please correct the errors below.")
    else:
        form = ProgramForm(instance=program)

    return render(
        request, "course/program_add.html", {"title": "Edit Program", "form": form}
    )


@login_required
@lecturer_required
def program_delete(request, pk):
    program = get_object_or_404(Program, pk=pk)
    program.delete()
    messages.success(request, f"Program '{program.title}' has been deleted.")
    return redirect("programs")


# ########################################################
# Course Views
# ########################################################

@login_required
def course_single(request, slug):
    course = get_object_or_404(Course, slug=slug)
    files = Upload.objects.filter(course=course)
    videos = UploadVideo.objects.filter(course=course)
    lecturers = CourseAllocation.objects.filter(courses=course)
    live_classes = LiveClass.objects.filter(course=course).order_by("-start_time")

    return render(
        request,
        "course/course_single.html",
        {
            "title": course.title,
            "course": course,
            "files": files,
            "videos": videos,
            "lecturers": lecturers,
            "live_classes": live_classes,  # Ensure live classes appear
            "media_url": settings.MEDIA_URL,
        },
    )


# ########################################################
# Course Admin Panel Views
# ########################################################

@login_required
@admin_required
def course_list_view(request):
    """Django admin-like list view with filters, search, pagination, bulk actions, and export"""
    # Export functionality
    if 'export' in request.GET and request.GET['export'] == 'csv':
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="courses.csv"'

        writer = csv.writer(response)
        writer.writerow(['Title', 'Code', 'Program', 'Level', 'Year', 'Semester', 'Elective', 'Credit'])

        filterset = CourseFilter(request.GET)
        queryset = filterset.qs.order_by('title')
        for course in queryset:
            writer.writerow([
                course.title, course.code, course.program.title, course.level,
                course.year, course.semester, course.is_elective, course.credit
            ])
        return response

    if request.method == "POST":
        action = request.POST.get('bulk_action')
        selected_courses = request.POST.getlist('selected_courses')

        if action and selected_courses:
            courses = Course.objects.filter(pk__in=selected_courses)
            if action == 'bulk_delete':
                deleted_count = courses.count()
                courses.delete()
                messages.success(request, f"Successfully deleted {deleted_count} course(s).")
            elif action == 'mark_elective':
                updated = courses.update(is_elective=True)
                messages.success(request, f"Marked {updated} course(s) as elective.")
            elif action == 'mark_core':
                updated = courses.update(is_elective=False)
                messages.success(request, f"Marked {updated} course(s) as core.")

        return redirect('course_list')

    # GET request - filtering and display
    filterset = CourseFilter(request.GET)
    queryset = filterset.qs

    # Ordering
    order_by = request.GET.get('o', 'title')
    if order_by.startswith('-'):
        queryset = queryset.order_by(order_by, 'title')
    else:
        queryset = queryset.order_by(order_by)

    # Pagination
    paginator = Paginator(queryset, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'filter': filterset,
        'filter.qs': page_obj,
        'title': "Courses",
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
        'order_by': order_by,
    }
    return render(request, "course/course_list.html", context)


@login_required
@admin_required
def course_add(request, pk):
    program = get_object_or_404(Program, pk=pk)

    if request.method == "POST":
        form = CourseAddForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.program = program  # Ensure program is assigned
            course.save()
            messages.success(request, f"Course '{course.title}' has been added.")
            return redirect("program_detail", pk=program.pk)
        messages.error(request, "Please correct the errors below.")
    else:
        form = CourseAddForm(initial={"program": program})

    return render(
        request,
        "course/course_add.html",
        {"title": "Add Course", "form": form, "program": program},
    )


@login_required
@admin_required
def course_edit(request, slug):
    course = get_object_or_404(Course, slug=slug)

    if request.method == "POST":
        form = CourseAddForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f"Course '{course.title}' has been updated.")
            return redirect("program_detail", pk=course.program.pk)
        messages.error(request, "Please correct the errors below.")
    else:
        form = CourseAddForm(instance=course)

    return render(
        request, "course/course_add.html", {"title": "Edit Course", "form": form}
    )


@login_required
@admin_required
def course_delete(request, slug):
    course = get_object_or_404(Course, slug=slug)
    course.delete()
    messages.success(request, f"Course '{course.title}' has been deleted.")
    return redirect("program_detail", pk=course.program.id)


@login_required
@admin_required
def course_add_admin(request):
    if request.method == "POST":
        form = CourseAddForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f"Course '{course.title}' has been added.")
            return redirect("course_list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = CourseAddForm()

    return render(
        request,
        "course/course_add.html",
        {"title": "Add Course", "form": form},
    )


@login_required
@admin_required
def course_edit_admin(request, slug):
    course = get_object_or_404(Course, slug=slug)

    if request.method == "POST":
        form = CourseAddForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f"Course '{course.title}' has been updated.")
            return redirect("course_list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = CourseAddForm(instance=course)

    return render(
        request, "course/course_add.html", {"title": "Edit Course", "form": form}
    )


@login_required
@admin_required
def course_delete_admin(request, slug):
    course = get_object_or_404(Course, slug=slug)
    course.delete()
    messages.success(request, f"Course '{course.title}' has been deleted.")
    return redirect("course_list")

@login_required
@admin_required
def course_history(request, slug):
    course = get_object_or_404(Course, slug=slug)
    # Use ActivityLog or Django's LogEntry
    logs = ActivityLog.objects.filter(
        message__icontains=f"Course '{course.title}'"
    ).order_by('-created_at')[:50]
    context = {
        'course': course,
        'logs': logs,
        'title': f"Change History for {course.title}",
    }
    return render(request, 'core/course_history.html', context)


# ########################################################
# Course Allocation Views
# ########################################################


@method_decorator([login_required, lecturer_required], name="dispatch")
class CourseAllocationFormView(CreateView):
    form_class = CourseAllocationForm
    template_name = "course/course_allocation_form.html"

    def form_valid(self, form):
        lecturer = form.cleaned_data["lecturer"]
        selected_courses = form.cleaned_data["courses"]
        allocation, created = CourseAllocation.objects.get_or_create(lecturer=lecturer)
        allocation.courses.set(selected_courses)
        messages.success(
            self.request,
            f"Courses allocated to {lecturer.get_full_name} successfully.",
        )
        return redirect("course_allocation_view")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Assign Course"
        return context


@method_decorator([login_required, lecturer_required], name="dispatch")
class CourseAllocationFilterView(FilterView):
    model = CourseAllocation
    filterset_class = CourseAllocationFilter
    template_name = "course/courseallocation_list.html"
    context_object_name = "course_allocations"
    paginate_by = 10


@login_required
@lecturer_required
def edit_allocated_course(request, pk):
    allocation = get_object_or_404(CourseAllocation, pk=pk)

    if request.method == "POST":
        form = EditCourseAllocationForm(request.POST, instance=allocation)
        if form.is_valid():
            form.save()
            messages.success(request, "Course allocation has been updated.")
            return redirect("course_allocation_view")
        messages.error(request, "Please correct the errors below.")
    else:
        form = EditCourseAllocationForm(instance=allocation)

    return render(
        request,
        "course/course_allocation_form.html",
        {"title": "Edit Course Allocation", "form": form},
    )


@login_required
@lecturer_required
def deallocate_course(request, pk):
    allocation = get_object_or_404(CourseAllocation, pk=pk)
    allocation.delete()
    messages.success(request, "Successfully deallocated courses.")
    return redirect("course_allocation_view")



# ########################################################
# File Upload Views
# ########################################################


@login_required
@lecturer_required
def handle_file_upload(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == "POST":
        form = UploadFormFile(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.course = course
            upload.save()
            messages.success(request, f"{upload.title} has been uploaded.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = UploadFormFile()
    return render(
        request,
        "upload/upload_file_form.html",
        {"title": "File Upload", "form": form, "course": course},
    )


@login_required
@lecturer_required
def handle_file_edit(request, slug, file_id):
    course = get_object_or_404(Course, slug=slug)
    upload = get_object_or_404(Upload, pk=file_id)
    if request.method == "POST":
        form = UploadFormFile(request.POST, request.FILES, instance=upload)
        if form.is_valid():
            upload = form.save()
            messages.success(request, f"{upload.title} has been updated.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = UploadFormFile(instance=upload)
    return render(
        request,
        "upload/upload_file_form.html",
        {"title": "Edit File", "form": form, "course": course},
    )


@login_required
@lecturer_required
def handle_file_delete(request, slug, file_id):
    upload = get_object_or_404(Upload, pk=file_id)
    title = upload.title
    upload.delete()
    messages.success(request, f"{title} has been deleted.")
    return redirect("course_detail", slug=slug)


# ########################################################
# Video Upload Views
# ########################################################


@login_required
@lecturer_required
def handle_video_upload(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == "POST":
        form = UploadFormVideo(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.course = course
            video.save()
            messages.success(request, f"{video.title} has been uploaded.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = UploadFormVideo()
    return render(
        request,
        "upload/upload_video_form.html",
        {"title": "Video Upload", "form": form, "course": course},
    )


@login_required
def handle_video_single(request, slug, video_slug):
    course = get_object_or_404(Course, slug=slug)
    video = get_object_or_404(UploadVideo, slug=video_slug)
    return render(
        request,
        "upload/video_single.html",
        {"video": video, "course": course},
    )


@login_required
@lecturer_required
def handle_video_edit(request, slug, video_slug):
    course = get_object_or_404(Course, slug=slug)
    video = get_object_or_404(UploadVideo, slug=video_slug)
    if request.method == "POST":
        form = UploadFormVideo(request.POST, request.FILES, instance=video)
        if form.is_valid():
            video = form.save()
            messages.success(request, f"{video.title} has been updated.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = UploadFormVideo(instance=video)
    return render(
        request,
        "upload/upload_video_form.html",
        {"title": "Edit Video", "form": form, "course": course},
    )


@login_required
@lecturer_required
def handle_video_delete(request, slug, video_slug):
    video = get_object_or_404(UploadVideo, slug=video_slug)
    title = video.title
    video.delete()
    messages.success(request, f"{title} has been deleted.")
    return redirect("course_detail", slug=slug)


# ########################################################
# Course Registration Views
# ########################################################


@login_required
@student_required
def course_registration(request):
    # Initialize all credit variables at the start
    total_first_semester_credit = 0
    total_sec_semester_credit = 0
    total_registered_credit = 0
    current_semester = None
    courses = Course.objects.none()
    registered_courses = Course.objects.none()

    if request.method == "POST":
        student = get_object_or_404(Student, student__id=request.user.id)
        course_ids = request.POST.getlist("course_ids")

        for course_id in course_ids:
            course = get_object_or_404(Course, pk=course_id)
            TakenCourse.objects.get_or_create(student=student, course=course)

        messages.success(request, "Courses registered successfully!")
        return redirect("course_registration")

    else:
        # Get current semester with error handling
        current_semester = Semester.objects.filter(is_current_semester=True).first()
        if not current_semester:
            messages.error(request, "No active semester found.")
            return render(request, "course/course_registration.html")

        # Get student and their taken courses
        student = get_object_or_404(Student, student__id=request.user.id)
        taken_courses = TakenCourse.objects.filter(student=student)
        taken_course_ids = [tc.course.id for tc in taken_courses]

        # Get available courses for registration
        courses = Course.objects.filter(
            program=student.program,
            level=student.level,
        ).exclude(id__in=taken_course_ids).order_by("year")

        # During add/drop period, show all eligible courses (removed department head dependency)

        # Calculate available course credits
        for course in courses:
            if course.semester == "First":
                total_first_semester_credit += course.credit
            elif course.semester == "Second":
                total_sec_semester_credit += course.credit

        # Get registered courses for current semester
        registered_courses = Course.objects.filter(
            id__in=taken_course_ids,
            semester=current_semester.semester
        )

        # Calculate registered credits
        total_registered_credit = sum(course.credit for course in registered_courses)



    context = {
        "current_semester": current_semester,
        "courses": courses,
        "registered_courses": registered_courses,
        "total_first_semester_credit": total_first_semester_credit,
        "total_sec_semester_credit": total_sec_semester_credit,
        "total_registered_credit": total_registered_credit,
        "student": student,
        "no_course_is_registered": registered_courses.count() == 0,
        "all_courses_are_registered": courses.count() == 0 and registered_courses.count() > 0,
        "is_calender_on": is_calender_on,
    }

    return render(request, "course/course_registration.html", context)



@login_required
@student_required
def course_drop(request):
    if request.method == "POST":
        student = get_object_or_404(Student, student__pk=request.user.id)
        course_ids = request.POST.getlist("course_ids")
        for course_id in course_ids:
            course = get_object_or_404(Course, pk=course_id)
            TakenCourse.objects.filter(student=student, course=course).delete()
        messages.success(request, "Courses dropped successfully!")
        return redirect("course_registration")


@login_required
@dep_head_required
def department_add_drop(request):
    from accounts.models import DepartmentHead
    dep_head = get_object_or_404(DepartmentHead, user=request.user)
    current_semester = Semester.objects.filter(is_current_semester=True).first()

    if not current_semester:
        messages.error(request, "No active semester found.")
        return redirect("dashboard")

    is_add_drop_open = current_semester.is_add_drop_open

    offer = CourseOffer.objects.filter(dep_head=dep_head).first()

    if request.method == "POST":
        if not is_add_drop_open:
            messages.error(request, "Add/Drop period is not active.")
            return redirect("department_add_drop")

        form = CourseOfferForm(request.POST, user=request.user, instance=offer)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.dep_head = dep_head
            offer.save()
            form.save_m2m()
            messages.success(request, "Offered courses updated successfully!")
            return redirect("department_add_drop")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CourseOfferForm(user=request.user, instance=offer)

    context = {
        "form": form,
        "current_semester": current_semester,
        "is_add_drop_open": is_add_drop_open,
        "dep_head": dep_head,
    }
    return render(request, "course/department_add_drop.html", context)


# ########################################################
# User Course List View
# ########################################################


@login_required
def user_course_list(request):
    if request.user.is_lecturer:
        courses = Course.objects.filter(allocated_course__lecturer__pk=request.user.id)
        return render(request, "course/user_course_list.html", {"courses": courses})

    if request.user.is_student:
        student = get_object_or_404(Student, student__pk=request.user.id)
        taken_courses = TakenCourse.objects.filter(student=student)
        return render(
            request,
            "course/user_course_list.html",
            {"student": student, "taken_courses": taken_courses},
        )

    # For other users
    return render(request, "course/user_course_list.html")


from .forms import CommentEditForm

@login_required
def discussion_list(request, slug):
    course = get_object_or_404(Course, slug=slug)
    discussions = Discussion.objects.filter(course=course)
    form = DiscussionForm()

    if request.method == "POST":
        form = DiscussionForm(request.POST)
        if form.is_valid():
            discussion = form.save(commit=False)
            discussion.course = course
            discussion.created_by = request.user
            discussion.save()
            messages.success(request, "Discussion started successfully.")
            return redirect("discussion_list", slug=slug)

    # Pass editable comments to the context
    comments = []
    for discussion in discussions:
        for comment in discussion.comments.all():
            comment.can_edit = comment.can_edit_or_delete(request.user)

    return render(
        request,
        "discussion/discussion_list.html",
        {
            "course": course,
            "discussions": discussions,
            "comments": comments,
            "form": form,
        },
    )


@login_required
def add_comment(request, discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id)
    parent_id = request.POST.get("parent")
    form = CommentForm(request.POST)
    

    if form.is_valid():
        comment = form.save(commit=False)
        comment.discussion = discussion
        comment.created_by = request.user
        
        if parent_id:
            parent_comment = Comment.objects.get(id=parent_id)
            comment.parent = parent_comment
            
        comment.save()
        messages.success(request, "Comment added successfully.")
    return redirect("discussion_list", slug=discussion.course.slug)

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if not comment.can_edit_or_delete(request.user):
        messages.error(request, "You don't have permission to edit this comment.")
        return redirect("discussion_list", slug=comment.discussion.course.slug)

    if request.method == "POST":
        form = CommentEditForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, "Comment updated successfully.")
            return redirect("discussion_list", slug=comment.discussion.course.slug)
    else:
        form = CommentEditForm(instance=comment)

    return render(request, "discussion/edit_comment.html", {"form": form, "comment": comment})

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if not comment.can_edit_or_delete(request.user):
        messages.error(request, "You don't have permission to delete this comment.")
        return redirect("discussion_list", slug=comment.discussion.course.slug)

    comment.delete()
    messages.success(request, "Comment deleted successfully.")
    return redirect("discussion_list", slug=comment.discussion.course.slug)

@login_required
def delete_discussion(request, discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id)

    if not discussion.can_delete(request.user):
        messages.error(request, "You don't have permission to delete this discussion.")
        return redirect("discussion_list", slug=discussion.course.slug)

    discussion.delete()
    messages.success(request, "Discussion deleted successfully.")
    return redirect("discussion_list", slug=discussion.course.slug)


from .models import LiveClass
from .forms import LiveClassForm
from datetime import datetime


@login_required
@lecturer_required
def create_live_class(request, slug):
    course = get_object_or_404(Course, slug=slug)

    if request.method == "POST":
        form = LiveClassForm(request.POST)
        
        if form.is_valid():
            date = request.POST.get("date")  # Get the date input
            time = request.POST.get("time")  # Get the time input

            if date and time:
                try:
                    # Combine date and time into a single datetime object
                    start_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
                    
                    # Save LiveClass instance
                    live_class = form.save(commit=False)
                    live_class.course = course
                    live_class.start_time = start_time  # Assign combined datetime
                    live_class.save()
                    
                    messages.success(request, "Live class scheduled successfully!")
                    return redirect("course_detail", slug=slug)
                except ValueError:
                    messages.error(request, "Invalid date or time format.")
            else:
                messages.error(request, "Please select both date and time.")

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = LiveClassForm()

    return render(request, "course/create_live_class.html", {"form": form, "course": course})



def live_class_detail(request, pk):
    live_class = get_object_or_404(LiveClass, pk=pk)
    return render(request, "course/live_class_detail.html", {"live_class": live_class})
