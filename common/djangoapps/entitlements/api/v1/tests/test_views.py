import json
import unittest
import uuid

from django.conf import settings
from django.core.urlresolvers import reverse
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from mock import patch

from entitlements.tests.factories import CourseEntitlementFactory
from entitlements.models import CourseEntitlement
from openedx.core.djangoapps.catalog import utils
from entitlements.api.v1.serializers import CourseEntitlementSerializer
from student.tests.factories import CourseEnrollmentFactory, UserFactory, TEST_PASSWORD
from student.models import CourseEnrollment


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EntitlementViewSetTest(ModuleStoreTestCase):
    ENTITLEMENTS_DETAILS_PATH = 'entitlements_api:v1:entitlements-detail'

    def setUp(self):
        super(EntitlementViewSetTest, self).setUp()
        self.user = UserFactory(is_staff=True)
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        self.course = CourseFactory()
        self.entitlements_list_url = reverse('entitlements_api:v1:entitlements-list')

    def _get_data_set(self, user, course_uuid):
        """
        Get a basic data set for an entitlement
        """
        return {
            "user": user.username,
            "mode": "verified",
            "course_uuid": course_uuid,
            "order_number": "EDX-1001"
        }

    def test_auth_required(self):
        self.client.logout()
        response = self.client.get(self.entitlements_list_url)
        assert response.status_code == 401

    def test_staff_user_required(self):
        not_staff_user = UserFactory()
        self.client.login(username=not_staff_user.username, password=UserFactory._DEFAULT_PASSWORD)
        response = self.client.get(self.entitlements_list_url)
        assert response.status_code == 403

    def test_add_entitlement_with_missing_data(self):
        entitlement_data_missing_parts = self._get_data_set(self.user, str(uuid.uuid4()))
        entitlement_data_missing_parts.pop('mode')
        entitlement_data_missing_parts.pop('course_uuid')

        response = self.client.post(
            self.entitlements_list_url,
            data=json.dumps(entitlement_data_missing_parts),
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_add_entitlement(self):
        course_uuid = uuid.uuid4()
        entitlement_data = self._get_data_set(self.user, str(course_uuid))

        response = self.client.post(
            self.entitlements_list_url,
            data=json.dumps(entitlement_data),
            content_type='application/json',
        )
        assert response.status_code == 201
        results = response.data

        course_entitlement = CourseEntitlement.objects.get(
            user=self.user,
            course_uuid=course_uuid
        )
        assert results == CourseEntitlementSerializer(course_entitlement).data

    def test_get_entitlements(self):
        entitlements = CourseEntitlementFactory.create_batch(2)

        response = self.client.get(
            self.entitlements_list_url,
            content_type='application/json',
        )
        assert response.status_code == 200

        results = response.data.get('results', [])
        assert results == CourseEntitlementSerializer(entitlements, many=True).data

    def test_get_user_entitlements(self):
        user2 = UserFactory()
        CourseEntitlementFactory.create()
        entitlement_user2 = CourseEntitlementFactory.create(user=user2)
        url = reverse('entitlements_api:v1:entitlements-list')
        url += '?user={username}'.format(username=user2.username)
        response = self.client.get(
            url,
            content_type='application/json',
        )
        assert response.status_code == 200

        results = response.data.get('results', [])
        assert results == CourseEntitlementSerializer([entitlement_user2], many=True).data

    def test_get_entitlement_by_uuid(self):
        entitlement = CourseEntitlementFactory()
        CourseEntitlementFactory.create_batch(2)

        CourseEntitlementFactory()
        url = reverse(self.ENTITLEMENTS_DETAILS_PATH, args=[str(entitlement.uuid)])

        response = self.client.get(
            url,
            content_type='application/json',
        )
        assert response.status_code == 200

        results = response.data
        assert results == CourseEntitlementSerializer(entitlement).data

    def test_delete_and_revoke_entitlement(self):
        course_entitlement = CourseEntitlementFactory()
        url = reverse(self.ENTITLEMENTS_DETAILS_PATH, args=[str(course_entitlement.uuid)])

        response = self.client.delete(
            url,
            content_type='application/json',
        )
        assert response.status_code == 204
        course_entitlement.refresh_from_db()
        assert course_entitlement.expired_at is not None

    def test_revoke_unenroll_entitlement(self):
        course_entitlement = CourseEntitlementFactory()
        url = reverse(self.ENTITLEMENTS_DETAILS_PATH, args=[str(course_entitlement.uuid)])

        enrollment = CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)

        course_entitlement.refresh_from_db()
        course_entitlement.enrollment_course_run = enrollment
        course_entitlement.save()

        assert course_entitlement.enrollment_course_run is not None

        response = self.client.delete(
            url,
            content_type='application/json',
        )
        assert response.status_code == 204

        course_entitlement.refresh_from_db()
        assert course_entitlement.expired_at is not None
        assert course_entitlement.enrollment_course_run is None


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
@patch("openedx.core.djangoapps.catalog.utils.get_course_runs_for_course")
class EntitlementEnrollmentViewSetTest(ModuleStoreTestCase):
    ENTITLEMENTS_ENROLLMENT_NAMESPACE = 'entitlements_api:v1:enrollments'

    def setUp(self):
        super(EntitlementEnrollmentViewSetTest, self).setUp()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        self.course = CourseFactory.create(org='edX', number='DemoX', display_name='Demo_Course')
        self.course2 = CourseFactory.create(org='edX', number='DemoX2', display_name='Demo_Course 2')

    def test_user_can_enroll(self, mock_get_course_runs):
        course_entitlement = CourseEntitlementFactory(
            user=self.user
        )
        url = reverse(
            self.ENTITLEMENTS_ENROLLMENT_NAMESPACE,
            args=[str(course_entitlement.uuid)]
        )
        assert course_entitlement.enrollment_course_run is None

        mock_get_course_runs.method.return_value = [
            {'key': str(self.course.id)}
        ]

        data = {
            'course_run_id': str(self.course.id)
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )
        course_entitlement.refresh_from_db()

        assert response.status_code == 201
        assert CourseEnrollment.is_enrolled(self.user, self.course.id)
        assert course_entitlement.enrollment_course_run is not None

    def test_user_can_unenroll(self, mock_get_course_runs):
        course_entitlement = CourseEntitlementFactory(
            user=self.user
        )
        url = reverse(
            self.ENTITLEMENTS_ENROLLMENT_NAMESPACE,
            args=[str(course_entitlement.uuid)]
        )
        assert course_entitlement.enrollment_course_run is None

        mock_get_course_runs.return_value = [
            {'key': str(self.course.id)}
        ]

        data = {
            'course_run_id': str(self.course.id)
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )
        course_entitlement.refresh_from_db()

        assert response.status_code == 201
        assert CourseEnrollment.is_enrolled(self.user, self.course.id)

        response = self.client.delete(
            url,
            content_type='application/json',
        )
        assert response.status_code == 204

        course_entitlement.refresh_from_db()
        assert not CourseEnrollment.is_enrolled(self.user, self.course.id)
        assert course_entitlement.enrollment_course_run is None

    def test_user_can_switch(self, mock_get_course_runs):
        course_entitlement = CourseEntitlementFactory(
            user=self.user
        )
        url = reverse(
            self.ENTITLEMENTS_ENROLLMENT_NAMESPACE,
            args=[str(course_entitlement.uuid)]
        )
        assert course_entitlement.enrollment_course_run is None

        mock_get_course_runs.return_value = [
            {'key': str(self.course.id)},
            {'key': str(self.course2.id)}
        ]

        data = {
            'course_run_id': str(self.course.id)
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )
        course_entitlement.refresh_from_db()

        assert response.status_code == 201
        assert CourseEnrollment.is_enrolled(self.user, self.course.id)

        data = {
            'course_run_id': str(self.course2.id)
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
        )
        assert response.status_code == 201

        course_entitlement.refresh_from_db()
        assert CourseEnrollment.is_enrolled(self.user, self.course2.id)
        assert course_entitlement.enrollment_course_run is not None
        print course_entitlement.enrollment_course_run.course_id
