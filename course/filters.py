from django.db.models import Q
import django_filters
from .models import Program, CourseAllocation, Course


class ProgramFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains", label="")

    class Meta:
        model = Program
        fields = ["title"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Change html classes and placeholders
        self.filters["title"].field.widget.attrs.update(
            {"class": "au-input", "placeholder": "Program name"}
        )


class CourseFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains", label="")
    code = django_filters.CharFilter(lookup_expr="icontains", label="")
    program = django_filters.CharFilter(method="filter_by_program", label="")
    search = django_filters.CharFilter(method="filter_search", label="Search")

    class Meta:
        model = Course
        fields = ["level", "year", "semester", "is_elective"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Change html classes and placeholders
        self.filters["search"].field.widget.attrs.update(
            {"class": "au-input", "placeholder": "Search courses..."}
        )
        self.filters["title"].field.widget.attrs.update(
            {"class": "au-input", "placeholder": "Course title"}
        )
        self.filters["code"].field.widget.attrs.update(
            {"class": "au-input", "placeholder": "Course code"}
        )
        self.filters["program"].field.widget.attrs.update(
            {"class": "au-input", "placeholder": "Program"}
        )

    def filter_by_program(self, queryset, name, value):
        return queryset.filter(program__title__icontains=value)

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            django_filters.Q(title__icontains=value) |
            django_filters.Q(code__icontains=value) |
            django_filters.Q(program__title__icontains=value)
        )


class CourseAllocationFilter(django_filters.FilterSet):
    lecturer = django_filters.CharFilter(method="filter_by_lecturer", label="")
    course = django_filters.filters.CharFilter(method="filter_by_course", label="")

    class Meta:
        model = CourseAllocation
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Change html classes and placeholders
        self.filters["lecturer"].field.widget.attrs.update(
            {"class": "au-input", "placeholder": "Lecturer"}
        )
        self.filters["course"].field.widget.attrs.update(
            {"class": "au-input", "placeholder": "Course"}
        )

    def filter_by_lecturer(self, queryset, name, value):
        return queryset.filter(
            Q(lecturer__first_name__icontains=value)
            | Q(lecturer__last_name__icontains=value)
        )

    def filter_by_course(self, queryset, name, value):
        return queryset.filter(courses__title__icontains=value)
