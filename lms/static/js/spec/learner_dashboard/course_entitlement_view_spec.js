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
            testSessionIds = ['test_session_id_1', 'test_session_id_2'];

        setupView = function(isAlreadyEnrolled) {
            setFixtures('<div class="course-entitlement-selection-container"></div>');

            self.initialSessionId = isAlreadyEnrolled ? testSessionIds[0] : '';
            self.entitlementAvailableSessions = [{
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
                el: '.course-entitlement-selection-container',
                triggerOpenBtn: '#course-card-0 .change-session',
                courseCardMessages: '#course-card-0 .messages-list > .message',
                courseTitleLink: '#course-card-0 .course-title a',
                courseImageLink: '#course-card-0 .wrapper-course-image > a',
                dateDisplayField: '#course-card-0 .info-date-block',
                enterCourseBtn: '#course-card-0 .enter-course',
                availableSessions: JSON.stringify(self.entitlementAvailableSessions),
                entitlementUUID: entitlementUUID,
                currentSessionId: self.initialSessionId,
                userId: '1',
                enrollUrl: '/api/enrollment/v1/enrollment',
                courseHomeUrl: '/courses/course-v1:edX+DemoX+Demo_Course/course/'
            });
        };

        afterEach(function() {
            if (view) view.remove();
        });

        describe('Initialization of view', function() {
            it('Should create a entitlement view element', function() {
                setupView(false);
                expect(view).toBeDefined();
            });
        });

        describe('Available Sessions Select - Unfulfilled Entitlement', function() {
            beforeEach(function() {
                setupView(false);
                self.select = view.$('.session-select');
                self.selectOptions = select.find('option');
            });

            it('Select session dropdown should show all available course runs and a coming soon option.', function() {
                expect(self.selectOptions.length).toEqual(self.entitlementAvailableSessions.length + 1);
            });

            it('Self paced courses should have visual indication in the selection option.', function() {
                var selfPacedOptionIndex = self.entitlementAvailableSessions.find( function(session, index) {
                    if (session.pacing_type === 'self-paced') return index;
                });
                var selfPacedOption = self.selectOptions[selfPacedOptionIndex];
                expect(selfPacedOption && selfPacedOption.text.includes('Self Paced')).toBe(true);
            });

            it('Courses with an enroll-by date should indicate so on the selection option.', function() {
                var enrollEndSetOptionIndex = self.entitlementAvailableSessions.find( function(session, index) {
                    if (session.enrollment_end !== 'null') return index;
                });
                var enrollEndSetOption = self.selectOptions[enrollEndSetOptionIndex];
                expect(enrollEndSetOption && enrollEndSetOption.text.includes('Enroll By') > -1).toBe(true);
            });

            it('Title element should correctly indicate the expected behavior.', function() {
                expect(view.$('.action-header').text().includes(
                    'In order to view the course you must select a session'
                )).toBe(true);
            });

            it('Change session button should have the correct text.', function() {
                expect(view.$('.enroll-btn-initial').text() === 'Select Session').toBe(true);
            });
        });

        describe('Available Sessions Select - Fulfilled Entitlement', function() {
            beforeEach(function() {
                setupView(true);
                self.select = view.$('.session-select');
                self.selectOptions = select.find('option');
            });

            it('Select session dropdown should show available course runs, coming soon and leave options.', function() {
                expect(self.selectOptions.length).toEqual(self.entitlementAvailableSessions.length + 2);
            });

            it('Select session dropdown should allow user to leave the current session.', function() {
                var leaveSessionOption = self.selectOptions[self.selectOptions.length - 1];
                expect(leaveSessionOption.text.includes('Leave current session and decide later.')).toBe(true);
            });

            it('Currently enrolled session should be specified in the dropdown options.', function() {
                var enrolledSessionIndex = self.entitlementAvailableSessions.find( function(session) {
                    return self.initialSessionId === session.session_id;
                });
                expect(self.selectOptions[enrolledSessionIndex].text.contains('(Currently Enrolled)')).toBe(true);
            });

            it('Title element should correctly indicate the expected behavior.', function() {
                expect(view.$('.action-header').text().includes(
                    'To change your session or leave your current session, please select from the following'
                )).toBe(true);
            });

            it('Change session button should have the correct text.', function() {
                expect(view.$('.enroll-btn-initial').text() === 'Change Session').toBe(true);
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
