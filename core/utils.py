import calendar
import random
import string
from django.utils.text import slugify
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import NewsAndEvents

def send_email(user, subject, msg):
    send_mail(
        subject,
        msg,
        settings.EMAIL_FROM_ADDRESS,
        [user.email],
        fail_silently=False,
    )


def send_html_email(subject, recipient_list, template, context):
    """A function responsible for sending HTML email"""
    # Render the HTML template
    html_message = render_to_string(template, context)

    # Generate plain text version of the email (optional)
    plain_message = strip_tags(html_message)

    # Send the email
    send_mail(
        subject,
        plain_message,
        settings.EMAIL_FROM_ADDRESS,
        recipient_list,
        html_message=html_message,
    )


def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


def unique_slug_generator(instance, new_slug=None):
    """
    Assumes the instance has a model with a slug field and a title
    character (char) field.
    """
    if new_slug is not None:
        slug = new_slug
    else:
        slug = slugify(instance.title)

    klass = instance.__class__
    qs_exists = klass.objects.filter(slug=slug).exists()
    if qs_exists:
        new_slug = f"{slug}-{random_string_generator(size=4)}"
        return unique_slug_generator(instance, new_slug=new_slug)
    return slug


class EventCalendar(calendar.HTMLCalendar):
    def __init__(self, events, *args, **kwargs):
        self.events = events
        super().__init__(*args, **kwargs)

    def formatday(self, day, weekday):
        if day != 0:
            cssclass = self.cssclasses[weekday]
            events_day = self.events.get(day, [])
            body = []
            if events_day:
                cssclass += ' event-day'
                for event in events_day:
                    body.append(f"<span class='event {event['type'].lower()}'>• {event['title']}</span>")
            content = '<span class="date">%d</span>' % day + ''.join(body)
            return '<td class="{}">{}</td>'.format(cssclass, content)
        return '<td class="noday">&nbsp;</td>'

    def formatmonthname(self, theyear, themonth, withyear=True):
        if withyear:
            s = '%s %s' % (calendar.month_name[themonth], theyear)
        else:
            s = '%s' % calendar.month_name[themonth]
        return '<tr><th colspan="7" class="month">%s</th></tr>' % s

    def formatmonth(self, theyear, themonth, withyear=True):
        v = []
        a = v.append
        a('<table border="0" cellpadding="0" cellspacing="0" class="calendar">')
        a('\n')
        a(self.formatmonthname(theyear, themonth, withyear))
        a('\n')
        a(self.formatweekheader())
        a('\n')
        for week in self.monthdays2calendar(theyear, themonth):
            a(self.formatweek(week))
            a('\n')
        a('</table>')
        a('\n')
        return ''.join(v)


def get_school_calendar(year, month):
    events_in_month = {}
    events = NewsAndEvents.objects.filter(event_date__year=year, event_date__month=month).exclude(event_date__isnull=True)
    for event in events:
        day = event.event_date.day
        if day not in events_in_month:
            events_in_month[day] = []
        events_in_month[day].append({'title': event.title, 'type': event.posted_as})
    cal = EventCalendar(events_in_month)
    return cal.formatmonth(year, month)


def get_school_calendar_with_navigation(year, month):
    """Enhanced calendar function that returns calendar with navigation context"""
    events_in_month = {}
    events = NewsAndEvents.objects.filter(event_date__year=year, event_date__month=month).exclude(event_date__isnull=True)
    for event in events:
        day = event.event_date.day
        if day not in events_in_month:
            events_in_month[day] = []
        events_in_month[day].append({'title': event.title, 'type': event.posted_as})

    cal = EventCalendar(events_in_month)
    calendar_html = cal.formatmonth(year, month)

    # Calculate previous and next months
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year = year - 1

    next_month = month + 1
    next_year = year
    if next_month == 13:
        next_month = 1
        next_year = year + 1

    return {
        'calendar_html': calendar_html,
        'current_year': year,
        'current_month': month,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'month_name': calendar.month_name[month],
        'events_count': events.count()
    }
