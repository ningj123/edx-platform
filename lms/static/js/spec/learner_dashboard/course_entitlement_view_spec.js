define([
    'backbone',
    'jquery',
    'js/learner_dashboard/models/course_entitlement_model',
    'js/learner_dashboard/views/course_entitlement_view'
], function(Backbone, $, CourseEntitlementModel, CourseEntitlementView) {
    'use strict';

    describe('Course Entitlement View', function() {
        var view = null,
            setupView,
            entitlementUUID = 'a9aiuw76a4ijs43u18',
            initialSessionId = '',
            testSessionIds = ['test_session_id_1', 'test_session_id_2'];

        beforeEach(function() {
            // continue;
        });

        setupView = function(isAlreadyEnrolled) {
            var entitlementAvailableSessions;

            setFixtures('<div class="course-entitlement-selection-container"></div>');

            initialSessionId = isAlreadyEnrolled ? testSessionIds[0] : '';
            entitlementAvailableSessions = [{
                enrollment_end: null,
                session_start: '2013-02-05T05:00:00+00:00',
                pacing_type: 'instructor_paced',
                session_id: testSessionIds[0],
                session_end: null
            }, {
                enrollment_end: '2017-12-22T03:30:00Z',
                session_start: '2018-01-03T13:00:00+00:00',
                pacing_type: 'self_paced',
                session_id: testSessionIds[1],
                session_end: '2018-03-09T21:30:00+00:00'
            }];

            view = new CourseEntitlementView({
                el: '#course-card-0 .course-entitlement-selection-container',
                triggerOpenBtn: '#course-card-0 .change-session',
                courseCardMessages: '#course-card-0 .messages-list > .message',
                courseTitleLink: '#course-card-0 .course-title a',
                courseImageLink: '#course-card-0 .wrapper-course-image > a',
                dateDisplayField: '#course-card-0 .info-date-block',
                enterCourseBtn: '#course-card-0 .enter-course',
                availableSessions: JSON.stringify(entitlementAvailableSessions),
                entitlementUUID: entitlementUUID,
                currentSessionId: initialSessionId,
                userId: '1',
                enrollUrl: '/api/enrollment/v1/enrollment',
                courseHomeUrl: '/courses/course-v1:edX+DemoX+Demo_Course/course/'
            });
        };

        afterEach(function() {
            if (view) view.remove();
        });

        describe('Visibility and initialization of view', function() {
            it('Should create a entitlement view element', function() {
                // setupView(false);
                // expect(view.el).toHaveClass('course-entitlement-selection-container');
            });

            it('Select session container should be visible when user has not yet selected a session.', function() {
                setupView(false);
                view.render();
                expect(view.$el.hasClass('hidden')).toBe(false);
            });

            it('Select session container should be hidden when user selected a session.', function() {
                // TODO: Implement this
                expect(true === false);
            });
        });

        describe('Available Sessions Select', function() {
            it('Select sessino dropdown should show all available course runs and a coming soon option.', function() {
                // TODO: Implement this
            });

            it('Self paced courses should have visual indication in the selection option.', function() {
                // TODO: Implement thisentitlement
            });

            it('Courses with an enroll-by date should indicate so on the selection option.', function() {
                // TODO: Implement this
            });

            it('If user is enrolled they should be able to leave current session/select a session later.', function() {
                // TODO: Implement this
            });

            it('Title element should correctly indicate the expected behavior.', function() {
                // TODO: Implement this
            });
        });

        describe('Change Session Action Button and popover behavior.', function() {
            it('Switch session button should correctly enable/disable when toggling available sessions.', function() {
                // TODO: Implement this
            });

            it('Switch session button should show correct call to action text when toggling sessions.', function() {
                // TODO: Implement this
            });

            it('Two step verification should show correct messaging depending on submission action.', function() {
                // TODO: Implement this
            });

            it('Clicking away from verification popover when it is visible should hide it.', function() {
                // TODO: Implement this
            });

            it('Clicking the cancel option from verification popover visible should hide it.', function() {
                // TODO: Implement this
            });

            it('Clicking the change session button should set focus to the first response option.', function() {
                // TODO: Implement this
            });
        });
    });
}
);
