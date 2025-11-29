from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import User, Student, Parent


def approve_registrations(modeladmin, request, queryset):
    """Bulk approve pending student registrations."""
    updated = queryset.filter(is_student=True, is_active=False).update(is_active=True)
    modeladmin.message_user(
        request,
        ngettext(
            '%d student registration was approved.',
            '%d student registrations were approved.',
            updated,
        ) % updated,
    )
approve_registrations.short_description = "Approve selected student registrations"


class UserAdmin(admin.ModelAdmin):
    list_display = [
        "get_full_name",
        "username",
        "email",
        "is_active",
        "is_student",
        "is_lecturer",
        "is_parent",
        "is_staff",
    ]
    search_fields = [
        "username",
        "first_name",
        "last_name",
        "email",
        "is_active",
        "is_lecturer",
        "is_parent",
        "is_staff",
    ]
    list_filter = [
        "is_active",
        "is_student",
        "is_lecturer",
        "is_parent",
        "is_staff",
    ]
    actions = [approve_registrations]

    def get_queryset(self, request):
        """Show inactive students by default for easier approval management."""
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            # Superusers see all users
            return queryset
        if 'is_active__exact=0' in request.GET.get('is_active__exact', '') or 'is_student__exact=1' in request.GET:
            # If filtering for inactive or students, respect the filter
            return queryset
        # Otherwise, show inactive students first for approval workflow
        return queryset.filter(is_student=True, is_active=False) | queryset.exclude(is_student=True)

    class Meta:
        managed = True
        verbose_name = "User"
        verbose_name_plural = "Users"


class StudentAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "level",
        "program",
        "get_is_active",
    ]
    list_filter = [
        ("student__is_active", admin.BooleanFieldListFilter),
    ]

    def get_is_active(self, obj):
        return obj.student.is_active
    get_is_active.short_description = _("Approved")
    get_is_active.admin_order_field = "student__is_active"
    get_is_active.boolean = True


admin.site.register(User, UserAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Parent)
