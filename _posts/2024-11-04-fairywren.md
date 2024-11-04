---
layout: post
title: "Scanning OSDI'24 | FairyWREN: A Sustainable Cache for Emerging Write-Read-Erase Flash Interfaces"
date: 2024-11-03 21:34:00
description: reading fairywren now
tags: flash-cache, osdi, scanning, paper
categories: sample-posts
featured: true
images:
  slider: true
---

发现CMU的flash cache三部曲（cachelib->kangaroo->fairywren）都发在osdi/sosp上，工作的连续性还是让我深感震惊和佩服。CMU真强 :-)

正在阅读中，后续推送一下

## 设计实现

（想把最头大的这部分先捋清楚...）

## 个人评价

- 技术写作还是很难懂的，如果之前没读过Kangaroo和CacheLib。很多细节略过，不知其所以然。
- 创新点真的太weak了，写来写去全是和kangaroo一个模子刻出来的。至少目前看起来，大小object分离、Fwlog和Fwset分层、冷热分离等等都是kangaroo提到过的。晦涩难懂又没创新。
- design开始看的真的折磨

## reference

- <a href="https://mp.weixin.qq.com/s/0g1jBn9SdE4QwygKx2qwQQ">【论文解读】数据中心节能减排：可持续的闪存缓存设计 FairyWREN (OSDI'24)</a>