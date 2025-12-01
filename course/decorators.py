# Calendar is considered on if there is a current semester configured
from core.models import Semester


def is_calender_on():
    """Check if calendar is on by verifying if there is an active current semester"""
    try:
        return Semester.objects.filter(is_current_semester=True).exists()
    except:
        # Database may not be ready during migrations or setup
        return False
