"""Test Entitlements helpers"""

from datetime import datetime, timedelta

from django.test import TestCase
import pytz

from student.tests.factories import (TEST_PASSWORD, CourseEnrollmentFactory,
                                     UserFactory)
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory

# Entitlements is not in CMS' INSTALLED_APPS so these imports will error during test collection
if settings.ROOT_URLCONF == 'lms.urls':
    from entitlements import helpers
    from entitlements.tests.factories import CourseEntitlementFactory, CourseEntitlementPolicyFactory


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestHelpers(TestCase):
    """Test entitlement with policy helper functions."""

    def setUp(self):
        super(TestHelpers, self).setUp()
        self.course = CourseOverviewFactory.create(
            start=datetime.utcnow()
        )
        self.user = UserFactory(is_staff=True)
        self.enrollment = CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)

    def test_is_entitlement_expired(self):
        """
        Test that the entitlement is not expired when created now, and is expired when created two years
        ago with a policy that sets the expiration period to 450 days
        """

        entitlement = CourseEntitlementFactory()
        policy = CourseEntitlementPolicyFactory()
        entitlement.policy = policy
        entitlement.save()

        assert helpers.is_entitlement_expired(entitlement) is False

        # Create a date 2 years in the past (greater than the policy expire period of 450 days)
        past_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(days=365 * 2)
        entitlement.created = past_datetime
        entitlement.save()
        entitlement.refresh_from_db()

        assert helpers.is_entitlement_expired(entitlement) is True

    def test_is_entitlement_refundable(self):
        """
        Test that the entitlement is refundable when created now, and is not refundable when created two years
        ago with a policy that sets the expiration period to 60 days
        """
        entitlement = CourseEntitlementFactory()
        policy = CourseEntitlementPolicyFactory()
        entitlement.policy = policy
        entitlement.save()
        assert helpers.is_entitlement_refundable(entitlement) is True

        # Create a date 2 years in the past (greater than the policy expire period of 60 days)
        past_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(days=365 * 2)
        entitlement.created = past_datetime
        # Make sure there isn't a course associated
        entitlement.enrollment_course_run = None
        entitlement.save()
        entitlement.refresh_from_db()

        assert helpers.is_entitlement_refundable(entitlement) is False

    def test_is_entitlement_regainable(self):
        """
        Test that the entitlement is not expired when created now, and is expired when created two years
        ago with a policy that sets the expiration period to 450 days
        """
        entitlement = CourseEntitlementFactory(enrollment_course_run=self.enrollment)
        policy = CourseEntitlementPolicyFactory()
        entitlement.policy = policy
        entitlement.save()
        assert helpers.is_entitlement_regainable(entitlement) is True

        # Create a date 2 years in the past (greater than the policy expire period of 14 days)
        # and apply it to both the entitlement and the course
        past_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(days=365 * 2)
        entitlement.created = past_datetime
        self.course.start = past_datetime

        entitlement.save()
        self.course.save()

        assert helpers.is_entitlement_regainable(entitlement) is False

    def test_get_days_until_expiration(self):
        """
        Test that the expiration period in days is always 1 less than the expiry period
        """
        entitlement = CourseEntitlementFactory(enrollment_course_run=self.enrollment)
        policy = CourseEntitlementPolicyFactory()
        entitlement.policy = policy
        entitlement.save()
        # This will always be 1 less than the expiration_period_days because the get_days_until_expiration
        # method will have had at least some time pass between object creation in setUp and this method execution
        assert (helpers.get_days_until_expiration(entitlement) == policy.expiration_period_days - 1)

