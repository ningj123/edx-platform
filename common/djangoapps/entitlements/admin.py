from django.contrib import admin

from .models import CourseEntitlement
from .models import CourseEntitlementPolicy


@admin.register(CourseEntitlement)
class EntitlementAdmin(admin.ModelAdmin):
    list_display = ('user',
                    'uuid',
                    'course_uuid',
                    'created',
                    'modified',
                    'expired_at',
                    'mode',
                    'enrollment_course_run',
                    'order_number')


@admin.register(CourseEntitlementPolicy)
class EntitlementPolicyAdmin(admin.ModelAdmin):
    list_display = ('expiration_period_days',
                    'refund_period_days',
                    'regain_period_days',
                    'site')
