from datetime import datetime, timedelta

import pytz
import sys
from django.conf import settings

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


def is_entitlement_expired(entitlement):
    """
    Determines from the policy if an entitlement can be redeemed, if it has not passed the
    expiration period of policy.expiration_period_days, and has not already been redeemed
    """
    utc = pytz.UTC
    days_since_created = (datetime.utcnow().replace(tzinfo=utc) - entitlement.created).days
    expiration_period = settings.ENTITLEMENTS_POLICY.get('expiration_period_days', sys.maxint)
    if entitlement.policy:
        expiration_period = entitlement.policy.expiration_period_days
    return days_since_created > expiration_period and not entitlement.enrollment_course_run


def is_entitlement_refundable(entitlement):
    """
    Determines from the policy if an entitlement can still be refunded, if the entitlement has not
    yet been redeemed (enrollment_course_run is NULL) and policy.refund_period_days has not yet passed
    """
    utc = pytz.UTC
    days_since_created = (datetime.utcnow().replace(tzinfo=utc) - entitlement.created).days
    refund_period = settings.ENTITLEMENTS_POLICY.get('refund_period_days', sys.maxint)
    if entitlement.policy:
        refund_period = entitlement.policy.expiration_period_days
    return (days_since_created < refund_period) and not entitlement.enrollment_course_run


def is_entitlement_regainable(entitlement):
    """
    Determines from the policy if an entitlement can still be regained by the user, if they choose
    to by leaving and regaining their entitlement within policy.regain_period_days days from start date of
    the course or their redemption, whichever comes later
    """
    if entitlement.enrollment_course_run:
        utc = pytz.UTC
        course_overview = CourseOverview.get_from_id(entitlement.enrollment_course_run.course_id)
        now = datetime.utcnow().replace(tzinfo=utc)
        regain_period = settings.ENTITLEMENTS_POLICY.get('regain_period_days', sys.maxint)
        if entitlement.policy:
            regain_period = entitlement.policy.expiration_period_days
        return (now - course_overview.start).days < regain_period or (now - entitlement.created).days < regain_period
    return False


def get_days_until_expiration(entitlement):
    """
    Returns an integer of number of days until the entitlement expires
    """
    expiration_period = settings.ENTITLEMENTS_POLICY.get('expiration_period_days', sys.maxint)
    if entitlement.policy:
        expiration_period = entitlement.policy.expiration_period_days
    expiry_date = entitlement.created + timedelta(expiration_period)
    utc = pytz.UTC
    now = datetime.utcnow().replace(tzinfo=utc)
    return (expiry_date - now).days
