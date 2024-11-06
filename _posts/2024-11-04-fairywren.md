---
layout: post
title: "Scanning OSDI'24 | FairyWREN: A Sustainable Cache for Emerging Write-Read-Erase Flash Interfaces"
date: 2024-11-03 21:34:00
description: reading fairywren now
tags: flash-cache, osdi, scanning, paper
categories: sample-posts
images:
  slider: true
---

发现CMU的flash cache三部曲（cachelib->kangaroo->fairywren）都发在osdi/sosp上，工作的连续性还是让我深感震惊和佩服。CMU真强 :-)

正在阅读中，后续推送一下

## 设计实现

（想把最头大的这部分先捋清楚...）

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/architecture.png" title="architecture" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    FairyWren系统结构
</div>


## 个人评价

- 技术写作还是很难懂的，如果之前没读过Kangaroo和CacheLib。很多细节略过，不知其所以然。
- 创新点真的太weak了，写来写去全是和kangaroo一个模子刻出来的。至少目前看起来，大小object分离、Fwlog和Fwset分层、冷热分离等等都是kangaroo提到过的。晦涩难懂又没创新。
- design开始看的真的折磨

## reference

- <a href="https://mp.weixin.qq.com/s/0g1jBn9SdE4QwygKx2qwQQ">【论文解读】数据中心节能减排：可持续的闪存缓存设计 FairyWREN (OSDI'24) </a>
- <a href="https://www.zhihu.com/question/649626302/answer/3596509565"> 2024年操作系统设计与实现研讨会（OSDI）有哪些值得关注的文章？--FairyWREN </a>
- <a href="https://zhuanlan.zhihu.com/p/708037149"> OSDI 2024 论文评述 Day 3 Session 9: Data Management | IPADS-SYS </a>