from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template, render_to_string
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django_filters.views import FilterView


from accounts.decorators import admin_required
from accounts.filters import LecturerFilter, StudentFilter
from accounts.forms import (
    EmailValidationOnForgotPassword,
    ParentAddForm,
    ProfileUpdateForm,
    ProgramUpdateForm,
    RegistrationForm,
    StaffAddForm,
    StudentAddForm,
)
from accounts.models import Parent, Student, User
from core.models import Semester, Session
from course.models import Course
from result.models import TakenCourse

# ########################################################
# Utility Functions
# ########################################################





# ########################################################
# Authentication and Registration
# ########################################################


def validate_username(request):
    username = request.GET.get("username", None)
    data = {"is_taken": User.objects.filter(username__iexact=username).exists()}
    return JsonResponse(data)


def registration_success(request):
    return render(request, "registration/registration_success.html")


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role')
            if role == 'student':
                messages.success(request, "Registration successful! Your account is pending approval. You will receive an email once approved.")
            elif role == 'lecturer':
                messages.success(request, "Registration successful! Your lecturer account is pending approval. You will receive an email once approved.")
            elif role == 'parent':
                messages.success(request, "Registration successful! Your parent account has been created.")
            return redirect("registration_success")
        # Form is invalid - the errors will be displayed via form fields and messages
        messages.error(
            request, "Please correct the errors below to complete your registration."
        )
    else:
        form = RegistrationForm()
    return render(request, "registration/register.html", {"form": form})


class CustomPasswordResetView(PasswordResetView):
    form_class = EmailValidationOnForgotPassword

    def form_valid(self, form):
        try:
            sent_emails = form.save()
            self.request.session['password_reset_email_sent'] = len(sent_emails or ()) > 0
        except Exception as e:
            # If saving fails, assume no emails were sent
            import logging
            logging.error(f"Password reset email failed: {e}")
            self.request.session['password_reset_email_sent'] = False
        return super().form_valid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['email_sent'] = self.request.session.pop('password_reset_email_sent', False)
        return context


# ########################################################
# Profile Views
# ########################################################


@login_required
def profile(request):
    """Show profile of the current user."""
    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()

    context = {
        "title": request.user.get_full_name,
        "current_session": current_session,
        "current_semester": current_semester,
    }

    if request.user.is_lecturer:
        courses = Course.objects.filter(
            allocated_course__lecturer__pk=request.user.id
        ).order_by("-year")
        context["courses"] = courses
        return render(request, "accounts/profile.html", context)

    if request.user.is_student:
        student = get_object_or_404(Student, student__pk=request.user.id)
        parent = Parent.objects.filter(student=student).first()
        courses = TakenCourse.objects.filter(
            student__student__id=request.user.id, course__level=student.level
        )
        context.update(
            {
                "parent": parent,
                "courses": courses,
                "level": student.level,
            }
        )
        return render(request, "accounts/profile.html", context)

    # For superuser or other staff
    staff = User.objects.filter(is_lecturer=True)
    context["staff"] = staff
    return render(request, "accounts/profile.html", context)


@login_required
@admin_required
def profile_single(request, user_id):
    """Show profile of any selected user."""
    if request.user.id == user_id:
        return redirect("profile")

    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()
    user = get_object_or_404(User, pk=user_id)

    context = {
        "title": user.get_full_name,
        "user": user,
        "current_session": current_session,
        "current_semester": current_semester,
    }

    if user.is_lecturer:
        courses = Course.objects.filter(
            allocated_course__lecturer__pk=user_id
        ).order_by("-year")
        context.update(
            {
                "user_type": "Lecturer",
                "courses": courses,
            }
        )
    elif user.is_student:
        student = get_object_or_404(Student, student__pk=user_id)
        courses = TakenCourse.objects.filter(
            student__student__id=user_id, course__level=student.level
        )
        context.update(
            {
                "user_type": "Student",
                "courses": courses,
                "student": student,
            }
        )
    else:
        context["user_type"] = "Superuser"

    return render(request, "accounts/profile_single.html", context)


@login_required
@admin_required
def admin_panel(request):
    return render(request, "setting/admin_panel.html", {"title": "Admin Panel"})


# ########################################################
# Settings Views
# ########################################################


@login_required
def profile_update(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("profile")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, "setting/profile_info_change.html", {"form": form})


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect("profile")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "setting/password_change.html", {"form": form})


# ########################################################
# Staff (Lecturer) Views
# ########################################################


@login_required
@admin_required
def staff_add_view(request):
    if request.method == "POST":
        form = StaffAddForm(request.POST)
        if form.is_valid():
            lecturer = form.save()
            full_name = lecturer.get_full_name
            email = lecturer.email
            messages.success(
                request,
                f"Account for lecturer {full_name} has been created. "
                f"An email with account credentials will be sent to {email} within a minute.",
            )
            return redirect("lecturer_list")
    else:
        form = StaffAddForm()
    return render(
        request, "accounts/add_staff.html", {"title": "Add Lecturer", "form": form}
    )


@login_required
@admin_required
def edit_staff(request, pk):
    lecturer = get_object_or_404(User, is_lecturer=True, pk=pk)
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=lecturer)
        if form.is_valid():
            form.save()
            full_name = lecturer.get_full_name
            messages.success(request, f"Lecturer {full_name} has been updated.")
            return redirect("lecturer_list")
        messages.error(request, "Please correct the error below.")
    else:
        form = ProfileUpdateForm(instance=lecturer)
    return render(
        request, "accounts/edit_lecturer.html", {"title": "Edit Lecturer", "form": form}
    )


@login_required
@admin_required
def lecturer_list_view(request):
    """Django admin-like lecturer list with filters, search, pagination, bulk actions, and export"""
    # Export functionality
    if 'export' in request.GET and request.GET['export'] == 'csv':
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="lecturers.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID No.', 'Full Name', 'Email', 'Phone', 'Address', 'Active', 'Last Login'])

        lecturers = User.objects.filter(is_lecturer=True).order_by('username')
        for lecturer in lecturers:
            writer.writerow([
                lecturer.username, lecturer.get_full_name(), lecturer.email,
                lecturer.phone, lecturer.address, lecturer.is_active, lecturer.last_login
            ])
        return response

    if request.method == "POST":
        action = request.POST.get('bulk_action')
        selected_lecturers = request.POST.getlist('selected_lecturers')

        if action and selected_lecturers:
            lecturers = User.objects.filter(pk__in=selected_lecturers, is_lecturer=True)
            if action == 'bulk_delete':
                deleted_count = lecturers.count()
                lecturers.delete()
                messages.success(request, f"Successfully deleted {deleted_count} lecturer(s).")
            elif action == 'bulk_activate':
                updated = lecturers.filter(is_active=False).update(is_active=True)
                messages.success(request, f"Activated {updated} lecturer(s).")
            elif action == 'bulk_deactivate':
                updated = lecturers.filter(is_active=True).update(is_active=False)
                messages.success(request, f"Deactivated {updated} lecturer(s).")

        return redirect('lecturer_list')

    # GET request - filtering and display
    filterset = LecturerFilter(request.GET, queryset=User.objects.filter(is_lecturer=True))
    queryset = filterset.qs

    # Ordering
    order_by = request.GET.get('o', 'username')
    if order_by.startswith('-'):
        queryset = queryset.order_by(order_by, 'username')
    else:
        queryset = queryset.order_by(order_by)

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'filter': filterset,
        'filter.qs': page_obj,
        'title': "Lecturers",
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
        'order_by': order_by,
    }
    return render(request, "accounts/lecturer_list.html", context)



@login_required
@admin_required
def delete_staff(request, pk):
    lecturer = get_object_or_404(User, is_lecturer=True, pk=pk)
    full_name = lecturer.get_full_name
    lecturer.delete()
    messages.success(request, f"Lecturer {full_name} has been deleted.")
    return redirect("lecturer_list")


@login_required
@admin_required
def approve_lecturer(request, pk):
    lecturer = get_object_or_404(User, is_lecturer=True, pk=pk)
    if lecturer.is_active:
        messages.warning(request, f"Lecturer {lecturer.get_full_name} is already approved.")
        return redirect("lecturer_list")

    if request.method == "POST":
        send_email = request.POST.get("send_email") == "on"
        lecturer.is_active = True
        lecturer.save(update_fields=['is_active'])

        if send_email:
            # Send login email
            from .utils import send_new_account_email, generate_lecturer_credentials
            username, password = generate_lecturer_credentials()
            lecturer.username = username
            lecturer.set_password(password)
            lecturer.save(update_fields=['username', 'password'])
            send_new_account_email(lecturer, password)
            messages.success(request, f"Lecturer {lecturer.get_full_name} has been approved and login email sent.")
        else:
            messages.success(request, f"Lecturer {lecturer.get_full_name} has been approved.")

        return redirect("lecturer_list")

    return render(request, "accounts/approve_lecturer.html", {"lecturer": lecturer})


# ########################################################
# Student Views
# ########################################################


@login_required
@admin_required
def student_add_view(request):
    if request.method == "POST":
        form = StudentAddForm(request.POST)
        if form.is_valid():
            student = form.save()
            # For admin-added students, approve immediately
            student.is_active = True
            student.is_student = True
            student.save(update_fields=['is_active', 'is_student'])
            full_name = student.get_full_name
            email = student.email
            messages.success(
                request,
                f"Account for {full_name} has been created. "
                f"An email with account credentials will be sent to {email} within a minute.",
            )
            return redirect("student_list")
        messages.error(request, "Correct the error(s) below.")
    else:
        form = StudentAddForm()
    return render(
        request, "accounts/add_student.html", {"title": "Add Student", "form": form}
    )


@login_required
@admin_required
def approve_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if student.student.is_active:
        messages.warning(request, f"Student {student.student.get_full_name} is already approved.")
        return redirect("student_list")

    if request.method == "POST":
        send_email = request.POST.get("send_email") == "on"
        student.student.is_active = True
        student.student.is_student = True
        student.student.save(update_fields=['is_active', 'is_student'])

        if send_email:
            # Send login email similar to signal
            from .utils import send_new_account_email, generate_student_credentials
            username, password = generate_student_credentials()
            student.student.username = username
            student.student.set_password(password)
            student.student.save(update_fields=['username', 'password'])
            send_new_account_email(student.student, password)
            messages.success(request, f"Student {student.student.get_full_name} has been approved and login email sent.")
        else:
            messages.success(request, f"Student {student.student.get_full_name} has been approved.")

        return redirect("student_list")

    return render(request, "accounts/approve_student.html", {"student": student})


@login_required
@admin_required
def edit_student(request, pk):
    student_user = get_object_or_404(User, is_student=True, pk=pk)
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=student_user)
        if form.is_valid():
            form.save()
            full_name = student_user.get_full_name
            messages.success(request, f"Student {full_name} has been updated.")
            return redirect("student_list")
        messages.error(request, "Please correct the error below.")
    else:
        form = ProfileUpdateForm(instance=student_user)
    return render(
        request, "accounts/edit_student.html", {"title": "Edit Student", "form": form}
    )


@method_decorator([login_required, admin_required], name="dispatch")
class StudentListView(FilterView):
    queryset = Student.objects.all()
    filterset_class = StudentFilter
    template_name = "accounts/student_list.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Students"
        return context



@login_required
@admin_required
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    full_name = student.student.get_full_name
    student.delete()
    messages.success(request, f"Student {full_name} has been deleted.")
    return redirect("student_list")


@login_required
@admin_required
def edit_student_program(request, pk):
    student = get_object_or_404(Student, student_id=pk)
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = ProgramUpdateForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            full_name = user.get_full_name
            messages.success(request, f"{full_name}'s program has been updated.")
            return redirect("profile_single", user_id=pk)
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = ProgramUpdateForm(instance=student)
    return render(
        request,
        "accounts/edit_student_program.html",
        {"title": "Edit Program", "form": form, "student": student},
    )


@login_required
@admin_required
def render_lecturer_pdf_list(request):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from django.conf import settings
    from django.core.files.storage import FileSystemStorage

    lecturers = User.objects.filter(is_lecturer=True).order_by('username')
    fname = "lecturers_list.pdf"
    flocation = settings.MEDIA_ROOT + "/lecturer_list/" + fname

    doc = SimpleDocTemplate(flocation, rightMargin=15, leftMargin=15, topMargin=15, bottomMargin=15)
    styles = getSampleStyleSheet()
    Story = []

    style = styles["Normal"]
    style.alignment = TA_CENTER
    style.fontName = "Helvetica-Bold"
    style.fontSize = 14
    title = Paragraph("Lecturers List", style)
    Story.append(title)
    Story.append(Spacer(1, 0.5 * inch))

    header = [("ID No.", "Full Name", "Email", "Phone", "Address", "Active")]
    table_header = Table(header, colWidths=[1.5*inch, 2.5*inch, 3*inch, 1.5*inch, 2*inch, 1*inch])
    table_header.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ])
    )
    Story.append(table_header)

    for lecturer in lecturers:
        data = [(
            lecturer.username,
            lecturer.get_full_name,
            lecturer.email,
            lecturer.phone or "",
            lecturer.address or "",
            "Yes" if lecturer.is_active else "No",
        )]
        t_body = Table(data, colWidths=[1.5*inch, 2.5*inch, 3*inch, 1.5*inch, 2*inch, 1*inch])
        t_body.setStyle(
            TableStyle([
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                ("ALIGN", (0, 5), (0, 5), "CENTER"),
            ])
        )
        Story.append(t_body)

    doc.build(Story)

    fs = FileSystemStorage(settings.MEDIA_ROOT + "/lecturer_list")
    with fs.open(fname) as pdf:
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = "inline; filename=" + fname
        return response
    return HttpResponse("Error generating PDF")


@login_required
@admin_required
def render_student_pdf_list(request):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from django.conf import settings
    from django.core.files.storage import FileSystemStorage

    students = Student.objects.all().order_by('student__username')
    fname = "students_list.pdf"
    flocation = settings.MEDIA_ROOT + "/student_list/" + fname

    doc = SimpleDocTemplate(flocation, rightMargin=15, leftMargin=15, topMargin=15, bottomMargin=15)
    styles = getSampleStyleSheet()
    Story = []

    style = styles["Normal"]
    style.alignment = TA_CENTER
    style.fontName = "Helvetica-Bold"
    style.fontSize = 14
    title = Paragraph("Students List", style)
    Story.append(title)
    Story.append(Spacer(1, 0.5 * inch))

    header = [("ID No.", "Full Name", "Email", "Phone", "Program", "Level", "Active")]
    table_header = Table(header, colWidths=[1.5*inch, 2.5*inch, 3*inch, 1.5*inch, 2*inch, 1*inch, 1*inch])
    table_header.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ])
    )
    Story.append(table_header)

    for student in students:
        data = [(
            student.student.username,
            student.student.get_full_name,
            student.student.email,
            student.student.phone or "",
            student.program.name if hasattr(student.program, 'name') else "",
            student.level,
            "Yes" if student.student.is_active else "No",
        )]
        t_body = Table(data, colWidths=[1.5*inch, 2.5*inch, 3*inch, 1.5*inch, 2*inch, 1*inch, 1*inch])
        t_body.setStyle(
            TableStyle([
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                ("ALIGN", (5, 0), (5, 0), "CENTER"),
                ("ALIGN", (6, 0), (6, 0), "CENTER"),
            ])
        )
        Story.append(t_body)

    doc.build(Story)

    fs = FileSystemStorage(settings.MEDIA_ROOT + "/student_list")
    with fs.open(fname) as pdf:
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = "inline; filename=" + fname
        return response
    return HttpResponse("Error generating PDF")


# ########################################################
# Parent Views
# ########################################################


@method_decorator([login_required, admin_required], name="dispatch")
class ParentAdd(CreateView):
    model = Parent
    form_class = ParentAddForm
    template_name = "accounts/parent_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Parent added successfully.")
        return super().form_valid(form)
