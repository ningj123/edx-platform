(function(define) {
    'use strict';

    define(['backbone',
        'jquery',
        'underscore',
        'gettext',
        'moment',
        'edx-ui-toolkit/js/utils/html-utils',
        'js/learner_dashboard/models/course_entitlement_model',
        'js/learner_dashboard/models/course_card_model',
        'text!../../../templates/learner_dashboard/course_entitlement.underscore'
    ],
         function(
             Backbone,
             $,
             _,
             gettext,
             moment,
             HtmlUtils,
             EntitlementModel,
             CourseCardModel,
             pageTpl
         ) {
             return Backbone.View.extend({
                 tpl: HtmlUtils.template(pageTpl),

                 events: {
                     'change .session-select': 'updateEnrollBtn',
                     'click .enroll-btn': 'handleEnrollChange',
                     'click .popover-dismiss': 'hideVerificationDialog',
                     'keydown .final-confirmation-btn': 'handleVerificationPopoverA11y'
                 },

                 initialize: function(options) {
                     this.$el = options.$el;

                     // Set up models and reload view on change
                     this.courseCardModel = new CourseCardModel();
                     this.entitlementModel = new EntitlementModel({
                         availableSessions: this.formatDates(JSON.parse(options.availableSessions)),
                         entitlementUUID: options.entitlementUUID,
                         currentSessionId: options.currentSessionId,
                         userId: options.userId
                     });
                     this.listenTo(this.entitlementModel, 'change', this.render);

                     // Grab URLs that handle changing of enrollment and entering a newly enrolled session.
                     this.enrollUrl = options.enrollUrl;
                     this.courseHomeUrl = options.courseHomeUrl;

                     // Grab elements from the parent card that work with this view and bind associated events
                     this.$triggerOpenBtn = options.$triggerOpenBtn; // Opens and closes session selection view
                     this.$dateDisplayField = options.$dateDisplayField; // Displays current session dates
                     this.$enterCourseBtn = options.$enterCourseBtn; // Button link to course home page
                     this.$courseTitleLink = options.$courseTitleLink; // Title link to course home page
                     this.$triggerOpenBtn.on('click', this.toggleSessionSelectionPanel.bind(this));

                     this.render(options);
                 },

                 render: function(options) {
                     HtmlUtils.setHtml(this.$el, this.tpl(this.entitlementModel.toJSON()));
                     this.delegateEvents();
                     this.updateEnrollBtn();
                 },

                 toggleSessionSelectionPanel: function(e) {
                    /*
                    Opens and closes the session selection panel.
                    */
                    this.$el.toggleClass('hidden');
                    if (!this.$el.hasClass('hidden')){
                        // Set focus to the session selection for a11y purposes
                        this.$('.session-select').focus();
                        this.$('.enroll-btn-initial').popover('hide');
                    }
                    this.updateEnrollBtn();
                 },

                 handleEnrollChange: function(e) {
                    /* Handles enrolling in a course, unenrolling in a session and changing session. */

                    // Grab the id for the desired session, an unenrollment event will return null
                    this.currentSessionSelection = this.$('.session-select').find('option:selected').data('session_id');

                    // Do not allow for enrollment when button is disabled
                    if (this.$('.enroll-btn-initial').hasClass('disabled')) return;

                    if (!this.currentSessionSelection) {
                        alert("We want to unenroll the user!");
                        return;
                    }

                    // Display the indicator icon
                    this.$dateDisplayField.html('<span class="fa fa-spinner fa-spin"></span>');

                    $.ajax({
                        type: 'POST',
                        url: this.enrollUrl,
                        contentType: 'application/json',
                        dataType: 'json',
                        data: JSON.stringify({
                            is_active: this.currentSessionSelection.length != 0,
                            course_details: {
                              course_id: this.currentSessionSelection,
                              course_uuid: this.entitlementModel.get('entitlementUUID'),
                            }
                          }),
                        success: _.bind(this.enrollSuccess, this),
                        error: _.bind(this.enrollError, this),
                    });
                 },

                 enrollSuccess: function(data) {
                    // Update external elements on the course card to represent the now available course session.
                    this.$triggerOpenBtn.removeClass('hidden');
                    this.$dateDisplayField.html(this.getAvailableSessionWithId(data.course_details.course_id).session_dates);
                    this.$dateDisplayField.prepend('<span class="fa fa-check"></span>');
                    this.$enterCourseBtn.attr('href', this.formatCourseHomeUrl(data.course_details.course_id));
                    this.$enterCourseBtn.removeClass('hidden');

                    // Update the model with the new session Id and close the selection panel.
                    this.entitlementModel.set({currentSessionId: this.currentSessionSelection});
                    this.toggleSessionSelectionPanel();
                 },

                 enrollError: function(data) {
                    this.$dateDisplayField.find('.fa.fa-spin').removeClass('fa-spin fa-spinner').addClass('fa-close');
                    this.$dateDisplayField.append(gettext('There was an error, please reload the page and try again.'));
                    this.hideVerificationDialog();
                 },

                 updateEnrollBtn: function() {
                    /*
                    This function is invoked on load, on opening the view and on changing the option on the session
                    selection dropdown. It plays three roles:
                    1) Enables and disables enroll button
                    2) Changes text to describe the action taken
                    3) Formats the confirmation popover to allow for two step authentication
                    */
                    var enrollText,
                        confirmationHTML,
                        currentSessionId = this.entitlementModel.get('currentSessionId'),
                        newSessionId = this.$('.session-select').find('option:selected').data('session_id'),
                        enrollBtnInitial = this.$('.enroll-btn-initial');

                    // Disable the button if the user is already enrolled in that session.
                    if (currentSessionId == newSessionId) {
                        enrollBtnInitial.addClass('disabled');
                        enrollBtnInitial.popover('dispose');
                        return;
                    }
                    enrollBtnInitial.removeClass('disabled');

                    // Update the button text based on whether the user is initially enrolling or changing session.
                    if (newSessionId) {
                        enrollText = currentSessionId ? gettext('Change Session') : gettext('Select Session');
                    } else {
                        enrollText = gettext("Leave Current Session");
                    }
                    this.$('.enroll-btn-initial').text(enrollText);

                    // Update the button popover to enable two step authentication.
                    if (newSessionId) {
                        confirmationHTML = currentSessionId ?
                            gettext('Are you sure that you would like to switch session?') + '<br><br>' +
                            gettext(' Please know that by choosing to switch session you will lose any progress you' +
                            'have made in this session.') :
                            gettext('Are you sure that you would like to select this session?');
                    } else {
                        confirmationHTML = gettext('Are you sure that you would like to leave this session?') +
                            '<br><br>' + gettext('Please know that by leaving you will lose any progress you had' +
                            ' made in this session.');
                    }

                    // Remove existing popover and re-initialize
                    enrollBtnInitial.popover('dispose');
                    enrollBtnInitial.popover({
                        placement: 'bottom',
                        container: this.$el,
                        html: true,
                        trigger: 'click',
                        content: '<div class="verification-modal" role="dialog"' +
                            'aria-labelledby="enrollment-verification-title">' +
                            '<p id="enrollment-verification-title">' + confirmationHTML + '</p>' +
                            '<div class="action-items">' +
                            '<button type="button" class="popover-dismiss final-confirmation-btn" tabindex="0">' +
                            gettext('No') + '</button>' +
                            '<button type="button" class="enroll-btn final-confirmation-btn" tabindex="0">' +
                            gettext('Yes') + '</button>' +
                            '</div>' + '</div>'
                    });

                    // Close popover on click-away
                    $(document).on('click', function(e) {
                       if (!($(e.target).closest('.enroll-btn-initial, .popover').length)){
                           this.$('.enroll-btn-initial').popover('hide');
                       };
                    }.bind(this));

                    // Ensure that focus moves to the popover on click of the initial change enrollment button.
                    this.$('.enroll-btn-initial').on('click', function() {
                        this.$('.final-confirmation-btn:first').focus();
                    }.bind(this));
                 },

                 handleVerificationPopoverA11y: function(e) {
                    /* Ensure that the second step verification popover is treated as an a11y compliant dialog */
                    var nextButton,
                        openButton = $(e.target).closest('.course-entitlement-selection-container')
                        .find('.enroll-btn-initial');
                    if (e.key == 'Tab') {
                        e.preventDefault();
                        nextButton = $(e.target).is(':first-child') ? $(e.target).next('.final-confirmation-btn') :
                            $(e.target).prev('.final-confirmation-btn');
                        nextButton.focus();
                    } else if (e.key == 'Escape') {
                        openButton.popover('hide');
                        openButton.focus();
                    }
                 },

                 hideVerificationDialog: function() {
                    this.$('.enroll-btn-initial').focus().popover('hide');
                 },

                 formatCourseHomeUrl: function(sessionId) {
                    /* Takes the base course home URL and updates it with the new session id*/
                    var newUrl = this.courseHomeUrl.split('/');
                    newUrl[newUrl.length-3] = sessionId;
                    return newUrl.join('/');
                 },

                 formatDates: function(sessionData) {
                    var startDate,
                        endDate,
                        dateFormat;
                    // Ensure the correct formatting for the date string
                    moment.locale(window.navigator.userLanguage || window.navigator.language);
                    dateFormat = moment.localeData().longDateFormat('L').indexOf('DD') >
                        moment.localeData().longDateFormat('L').indexOf('MM') ? 'MMMM D, YYYY' : 'D MMMM, YYYY';

                    for (var i = 0; i < sessionData.length; i++) {
                        startDate = sessionData[i].session_start ?
                            moment((new Date(sessionData[i].session_start))).format(dateFormat) : null;
                        endDate = sessionData[i].session_end ?
                            moment((new Date(sessionData[i].session_end))).format(dateFormat) : null;
                        sessionData[i].session_dates = this.courseCardModel.formatDateString({
                            'start_date': startDate,
                            'end_date': endDate,
                            'pacing_type': sessionData[i].pacing_type
                        });
                        sessionData[i].enrollmentEndDate =  sessionData[i].enrollment_end ?
                            moment((new Date(sessionData[i].enrollment_end))).format(dateFormat) : null;
                    }
                    return sessionData;
                 },

                 getAvailableSessionWithId: function(sessionId) {
                     /* Returns an available session given a sessionId */
                    var available_sessions = this.entitlementModel.get('availableSessions').filter(function(x) {
                        return x.session_id == sessionId
                    });
                    return available_sessions ? available_sessions[0] : '';
                 }
             });
         }
    );
}).call(this, define || RequireJS.define);
