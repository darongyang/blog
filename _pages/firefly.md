---
layout: page
title: firefly
permalink: /firefly/
nav: true
nav_order: 4

news: false # includes a list of news items
selected_papers: false # includes a list of papers marked as "selected={true}"
social: false# includes social icons at the bottom of the page
---

<div class="row mt-3 day-content">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/honkai-2.png" title="Firefly's Secret Base" class="img-fluid rounded z-depth-1" %}
        <div class="caption">
            Firefly's Secret Base in Dream's Edge
        </div>
    </div>
</div>


<div class="row mt-3 day-content">
    <div class="col-sm mt-3 mt-md-0">
        {% include audio.liquid path="assets/audio/neverhurt.mp3" loop=true autoplay=true id="day-audio" %}
    </div>
</div>

<div class="row mt-3 night-content">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/honkai.png" title="Fly with Firefly" class="img-fluid rounded z-depth-1" %}
        <div class="caption">
            Fly in the Sky with Firefly
        </div>
    </div>
</div>

<div class="row mt-3 night-content">
    <div class="col-sm mt-3 mt-md-0">
        {% include audio.liquid path="assets/audio/neversun.mp3" loop=true autoplay=true id="night-audio" %}
    </div>
</div>

<script>
document.addEventListener("DOMContentLoaded", function() {
    const dayAudio = document.getElementById("day-audio");
    const nightAudio = document.getElementById("night-audio");

    // 初始设置，根据系统主题播放对应的音频
    function applyThemeBasedOnSystemPreference() {
        const isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
        consule.log(isDarkMode)
        if (isDarkMode) {
            nightAudio.play();
            dayAudio.pause();
        } else {
            dayAudio.play();
            nightAudio.pause();
        }
    }

    applyThemeBasedOnSystemPreference()d
});
</script> 

