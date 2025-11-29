# Calendar is considered on if there is a current semester configured
from core.models import Semester

# Calendar is on if there is an active semester
is_calender_on = Semester.objects.filter(is_current_semester=True).exists()
