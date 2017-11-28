import uuid as uuid_tools
from datetime import datetime, timedelta

import pytz
from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models

from model_utils.models import TimeStampedModel
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class CourseEntitlementPolicy(models.Model):
    """
    Represents the Entitlement's policy for expiration, refunds, and regaining a used certificate
    """

    expiration_period_days = models.IntegerField(
        default=450,
        help_text="Number of days from when an entitlement is created until when it is expired.",
        null=False
    )
    refund_period_days = models.IntegerField(
        default=60,
        help_text="Number of days from when an entitlement is created until when it is no longer refundable.",
        null=False
    )
    regain_period_days = models.IntegerField(
        default=14,
        help_text="Number of days from when an entitlement is created until " +
                  "when it is no longer able to be regained by a user.",
        null=False
    )
    site = models.ForeignKey(Site)


class CourseEntitlement(TimeStampedModel):
    """
    Represents a Student's Entitlement to a Course Run for a given Course.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    uuid = models.UUIDField(default=uuid_tools.uuid4, editable=False)
    course_uuid = models.UUIDField(help_text='UUID for the Course, not the Course Run')
    expired_at = models.DateTimeField(
        null=True,
        help_text='The date that an entitlement expired, if NULL the entitlement has not expired.',
        blank=True
    )
    mode = models.CharField(max_length=100, help_text='The mode of the Course that will be applied on enroll.')
    enrollment_course_run = models.ForeignKey(
        'student.CourseEnrollment',
        null=True,
        help_text='The current Course enrollment for this entitlement. If NULL the Learner has not enrolled.'
    )
    order_number = models.CharField(max_length=128, null=True)
    _policy = models.ForeignKey(CourseEntitlementPolicy, null=True, blank=True)

    @property
    def expired_at_datetime(self):
        if not self.expired_at and self.is_entitlement_redeemable():
            self.expired_at = datetime.utcnow()
            self.save()
        return self.expired_at

    @property
    def policy(self):
        return self._policy or CourseEntitlementPolicy()

    @policy.setter
    def policy(self, value):
        self._policy = value

    def get_days_since_created(self):
        """
        Returns an integer of number of days since the entitlement has been created
        """
        utc = pytz.UTC
        return (datetime.now(tz=utc) - self.created).days

    def get_days_until_expiration(self):
        """
        Returns an integer of number of days until the entitlement expires
        """
        expiry_date = self.created + timedelta(self.policy.expiration_period_days)
        now = datetime.now(tz=pytz.UTC)
        return (expiry_date - now).days

    def is_entitlement_regainable(self):
        """
        Determines from the policy if an entitlement can still be regained by the user, if they choose
        to by leaving and regaining their entitlement within policy.regain_period_days days from start date of
        the course or their redemption, whichever comes later
        """
        if self.enrollment_course_run:
            now = datetime.now(tz=pytz.UTC)
            course_overview = CourseOverview.get_from_id(self.enrollment_course_run.course_id)
            return ((now - course_overview.start).days < self.policy.regain_period_days or
                    (now - self.enrollment_course_run.created).days < self.policy.regain_period_days)
        return False

    def is_entitlement_refundable(self):
        """
        Determines from the policy if an entitlement can still be refunded, if the entitlement has not
        yet been redeemed (enrollment_course_run is NULL) and policy.refund_period_days has not yet passed
        """
        return (self.get_days_since_created() < self.policy.refund_period_days) and not self.enrollment_course_run

    def is_entitlement_redeemable(self):
        """
        Determines from the policy if an entitlement can be redeemed, if it has not passed the
        expiration period of policy.expiration_period_days, and has not already been redeemed
        """
        return self.get_days_since_created() < self.policy.expiration_period_days and not self.enrollment_course_run
