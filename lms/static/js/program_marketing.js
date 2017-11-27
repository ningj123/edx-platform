function playVideo(src) {
    'use strict';
    document.querySelector('#program_video button').style = 'display:none;';
    document.querySelector('#program_video iframe').style = 'display:block;';
    document.querySelector('#program_video iframe').src = src;
}
function expandFAQ(link, faq_hash){
    var faq_preview_el = document.getElementById("preview-answer-" + faq_hash)
    var faq_complete_el = document.getElementById("complete-answer-" + faq_hash)
    link.classList.add("hidden")
    faq_preview_el.classList.add("hidden")
    faq_complete_el.classList.remove("hidden")
}