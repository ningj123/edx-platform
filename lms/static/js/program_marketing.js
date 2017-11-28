function playVideo(src) {
    'use strict';
    document.querySelector('#program_video button').style = 'display:none;';
    document.querySelector('#program_video iframe').style = 'display:block;';
    document.querySelector('#program_video iframe').src = src;
}
function expandFAQ(currentElement, faqHash) {
    'use strict';
    var link = currentElement;
    var faqPreviewElement = document.getElementById('preview-answer-' + faqHash);
    var faqCompleteElement = document.getElementById('complete-answer-' + faqHash);
    link.classList.add('hidden');
    faqPreviewElement.classList.add('hidden');
    faqCompleteElement.classList.remove('hidden');
}
