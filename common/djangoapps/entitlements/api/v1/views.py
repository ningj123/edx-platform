import logging

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from edx_rest_framework_extensions.authentication import JwtAuthentication
from opaque_keys.edx.keys import CourseKey
from rest_framework import permissions, viewsets, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from student.models import CourseEnrollmentException
# from enrollment.errors import CourseEnrollmentError, CourseEnrollmentExistsError, CourseModeNotFoundError
# from openedx.core.lib.exceptions import CourseNotFoundError

from entitlements.api.v1.filters import CourseEntitlementFilter
from entitlements.api.v1.serializers import CourseEntitlementSerializer
from entitlements.models import CourseEntitlement
from openedx.core.djangoapps.catalog.utils import get_course_runs_for_course
from student.models import CourseEnrollment

log = logging.getLogger(__name__)


class EntitlementViewSet(viewsets.ModelViewSet):
    authentication_classes = (JwtAuthentication, SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser,)
    queryset = CourseEntitlement.objects.all().select_related('user')
    lookup_value_regex = '[0-9a-f-]+'
    lookup_field = 'uuid'
    serializer_class = CourseEntitlementSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = CourseEntitlementFilter

    def perform_destroy(self, instance):
        """
        This method is an override and is called by the DELETE method
        """
        save_model = False
        if instance.expired_at is None:
            instance.expired_at = timezone.now()
            log.info('Set expired_at to [%s] for course entitlement [%s]', instance.expired_at, instance.uuid)
            save_model = True

        if instance.enrollment_course_run is not None:
            CourseEnrollment.unenroll(
                user=instance.user,
                course_id=instance.enrollment_course_run.course_id,
                skip_refund=True
            )
            enrollment = instance.enrollment_course_run
            instance.enrollment_course_run = None
            save_model = True
            log.info(
                'Unenrolled user [%s] from course run [%s] as part of revocation of course entitlement [%s]',
                instance.user.username,
                enrollment.course_id,
                instance.uuid
            )
        if save_model:
            instance.save()


class EntitlementEnrollmentViewSet(viewsets.GenericViewSet):
    authentication_classes = (JwtAuthentication, SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = CourseEntitlement.objects.all()
    serializer_class = CourseEntitlementSerializer

    def _verify_course_run_for_entitlement(self, entitlement, course_session_id):
        course_run_valid = False
        course_runs = get_course_runs_for_course(entitlement.course_uuid)
        for run in course_runs:
            if course_session_id == run.get('key', ''):
                course_run_valid = True
                break
        return course_run_valid

    def _enroll_entitlement(self, entitlement, course_session_key, user):
        try:
            enrollment = CourseEnrollment.enroll(
                user=user,
                course_key=course_session_key,
                mode=entitlement.mode,
            )
        except CourseEnrollmentException:
            message = (
                'Course Entitlement Enroll for {username} failed for course: {course_id}, '
                'mode: {mode}, and entitlement: {entitlement}'
            ).format(
                username=user.username,
                course_id=course_session_key,
                mode=entitlement.mode,
                entitlement=entitlement.uuid
            )
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'message': message}
            )

        CourseEntitlement.set_enrollment(entitlement, enrollment)

    def _unenroll_entitlement(self, entitlement, course_session_key, user):
        CourseEnrollment.unenroll(user, course_session_key, skip_refund=True)
        CourseEntitlement.set_enrollment(entitlement, None)

    def create(self, request, uuid):
        course_session_id = request.data.get('course_run_id', None)

        if not course_session_id:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data="The Course Run ID was not provided."
            )

        # Verify that the user has an Entitlement for the provided Course UUID.
        try:
            entitlement = CourseEntitlement.objects.get(uuid=uuid, user=request.user, expired_at=None)
        except CourseEntitlement.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data="The Entitlement for this UUID does not exist or is Expired."
            )

        # Verify the course run ID is of the same type as the Course entitlement.
        course_run_valid = self._verify_course_run_for_entitlement(entitlement, course_session_id)
        if not course_run_valid:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'message': "The Course Run ID is not a match for this Course Entitlement."
                }
            )

        # Determine if this is a Switch session or a simple enroll and handle both.
        try:
            course_run_string = CourseKey.from_string(course_session_id)
        except CourseKey.InvalidKeyError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'message': u"Invalid '{course_id}'".format(course_id=course_session_id)
                }
            )
        if entitlement.enrollment_course_run is None:
            self._enroll_entitlement(
                entitlement=entitlement,
                course_session_key=course_run_string,
                user=request.user
            )
        elif entitlement.enrollment_course_run.course_id != course_session_id:
            self._unenroll_entitlement(
                entitlement=entitlement,
                course_session_key=entitlement.enrollment_course_run.course_id,
                user=request.user
            )
            self._enroll_entitlement(
                entitlement=entitlement,
                course_session_key=course_run_string,
                user=request.user
            )

        return Response(
            status=status.HTTP_201_CREATED,
            data={
                'uuid': entitlement.uuid,
                'course_run_id': course_session_id,
                'is_active': True
            }
        )

    def destroy(self, request, uuid):
        """
        On DELETE call to this API we will unenroll the course enrollment for the provided uuid
        """
        try:
            entitlement = CourseEntitlement.objects.get(uuid=uuid, user=request.user, expired_at=None)
        except CourseEntitlement.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data="The Entitlement for this UUID does not exist or is Expired."
            )

        if entitlement.enrollment_course_run is None:
            return Response(status=status.HTTP_204_NO_CONTENT)

        self._unenroll_entitlement(
            entitlement=entitlement,
            course_session_key=entitlement.enrollment_course_run.course_id,
            user=request.user
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
