---
layout: post
title: FEMU Timing Model Analysis
date: 2024-10-18 21:34:00
description: an example of a blog post with some test
tags: ssd-simulator
categories: sample-posts
featured: true
images:
  slider: true
---

起因是我改变nand.h里TLC的时延，发现ocssd 1.2的fio性能没有任何变化。我感觉应该是femu的ocssd1.2自身时延模拟的问题。我打算研究一下femu的时延模拟这个方面。

（更新中...）

## nvme.h

重要结构体：

- `struct FemuCtrl`，整个femu的全局字段。
- `struct NvmeRequest`，每个请求的相关字段。

## nand.h

## timing.c

- 函数`set_latency`

根据全局的`FemuCtrl *n`设置时延有关的字段，如`n->upg_rd_lat_ns = ...`。

- 函数`advance_channel_timestmap`

根据传入的当前时间`now`，通道编号`id`，和本次操作的类型`opcode`，以及当前通道的状态`n->chnl_locks[ch]`，来更新通道编号`id`的通道下一次可以使用的时间。目前这个函数直接返回了`now`。

但根据提供的剩下代码来看，其主要思路大致描述为：（1）获取当前操作的通道可用时间。如果当前的通道是可用状态（即，`now>=n->chnl_next_avail_time[ch]`），则直接可用（即，`start_data_xfer_ts=now`）；否则会等待到可用时间。（2）更新下次操作的通道可用时间。如果当前操作是`erase`操作，通道无需做页面传输，直接可用；否则为`read`或`write`操作时，还需要等待页面传输结束（即，`n->chnl_pg_xfer_lat_ns * 2`的时间）。

（疑惑：但是为什么要乘以2，这个不太能理解，可能是出于数据传输可靠性的考虑？）
