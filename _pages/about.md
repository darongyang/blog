---
layout: about
title: about
permalink: /
# subtitle: A paper a day, the reject away~
subtitle: New to Storage! Star Rail Firefly Lover!

profile:
  align: right
  image: gucao.png
  image_circular: false # crops the image to make it circular
  more_info: >
    <p>📍&nbsp;Shenzhen, China</p>
    <p>📧 darongyang@foxmail.com</p>
    <p>🎓 Master's candidate</p>
    <p>🏫 <a href='https://www.hitsz.edu.cn/index.html'>Harbin Institute of Technology, Shenzhen</a></p>

news: false # includes a list of news items
selected_papers: false # includes a list of papers marked as "selected={true}"
social: false# includes social icons at the bottom of the page
---

The work I have been engaged in recently:

- Exams of Required Courses
- A Immature work on High-density Flash Memory
- Investigation in `AI Pipeline and Storage`
  - [ ] G10 (MICRO'23)
  - [ ] vLLM (SOSP'23)
  - [ ] CachedAttention (ATC'24)
  - [ ] and etc
- Reading and Summary in `Flash Cache`
  - [ ] CacheLib (OSDI'20)
  - [ ] Kangaroo (SOSP'21) -> Scanning Now.
  - [ ] FairyWREN (OSDI'24)
  - [ ] CSAL (EuroSys'24) -> √ Finish Scanning. To Update.
  - [ ] Baleen (FAST'24)
  - [ ] Austere (ATC'20)
  - [ ] and etc
- Reading and Summary in `Partital FTL with Learning`
  - [ ] LeaFTL(ASPLOS'23) -> May Skim Next Week
  - [ ] LearnedFTL(HPCA'24)
  - [ ] and etc
- Try to Find Other Area on `Traditional Flash Storage`
  - ZNS or High-Density SSD or Dedup? However, I think it's hard :-)
- May Participate in a Work about MOE?

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
        {% include audio.liquid path="assets/audio/neverhurt.mp3" loop=true autoplay=true id="day-audio"%}
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
        if (isDarkMode) {
            nightAudio.play();
            dayAudio.pause();
        } else {
            dayAudio.play();
            nightAudio.pause();
        }
    }
    // 切换主题时播放对应音频
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute("data-theme");
        const newTheme = currentTheme === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", newTheme);

        if (newTheme === "dark") {
            dayAudio.pause();
            nightAudio.play();
        } else {
            nightAudio.pause();
            dayAudio.play();
        }
    }

    // 初始调用，检查并设置系统主题
    applyThemeBasedOnSystemPreference();

    // 监听系统主题变更（适用于系统主题变化时）
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener("change", (e) => {
        if (e.matches) {
            document.documentElement.setAttribute("data-theme", "dark");
            dayAudio.pause();
            nightAudio.play();
        } else {
            document.documentElement.setAttribute("data-theme", "light");
            nightAudio.pause();
            dayAudio.play();
        }
    });

    // 为手动切换主题添加事件监听器
    document.getElementById("theme-toggle-btn").addEventListener("click", toggleTheme);
});
</script>