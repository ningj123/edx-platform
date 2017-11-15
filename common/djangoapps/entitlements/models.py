import uuid as uuid_tools
from datetime import datetime

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models

from entitlements.helpers import is_entitlement_expired
from model_utils.models import TimeStampedModel


class CourseEntitlementManager(models.Manager):
    def get_queryset(self):
        queryset = super(CourseEntitlementManager, self).get_queryset()
        for entitlement in queryset:
            if not entitlement.expired_at and is_entitlement_expired(entitlement):
                entitlement.expired_at = datetime.utcnow()
                entitlement.save()
        return queryset


class CourseEntitlementPolicy(models.Model):
    """
    Represents the Entitlement's policy for expiration, refunds, and regaining a used certificate
    """

    expiration_period_days = models.IntegerField(
        default=450,
        help_text="Number of days from when an entitlement is created until when it is expired."
    )
    refund_period_days = models.IntegerField(
        default=60,
        help_text="Number of days from when an entitlement is created until when it is no longer refundable."
    )
    regain_period_days = models.IntegerField(
        default=14,
        help_text="Number of days from when an entitlement is created until " +
                  "when it is no longer able to be regained by a user."
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
        help_text='The date that an entitlement expired, if NULL the entitlement has not expired.'
    )
    mode = models.CharField(max_length=100, help_text='The mode of the Course that will be applied on enroll.')
    enrollment_course_run = models.ForeignKey(
        'student.CourseEnrollment',
        null=True,
        help_text='The current Course enrollment for this entitlement. If NULL the Learner has not enrolled.'
    )
    order_number = models.CharField(max_length=128, null=True)
    policy = models.ForeignKey(CourseEntitlementPolicy, null=True)
    objects = CourseEntitlementManager()
