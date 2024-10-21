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

## femu论文

从 3.2 Accuracy 开始

### 时延实现

在femu中，数据传输和时延模拟相解耦。

- 数据传输：I/O请求到达时，femu会直接通过DMA方式完成读写的数据传输。
- 时延模拟：（1）传输数据的时候，femu会用计算出来的模拟时延$$ latency $$来得到请求结束时间$$ T_{endio} $$，并用$$ T_{endio} $$标记这个I/O请求，将这个请求插入到按照$$ T_{endio} $$作为优先级的endio队列中。（2）femu专门有一个线程用于处理endio队列，当队列中I/O请求所记录的完成时间$$ T_{endio} $$大于等于现在时间$$ T_{now} $$时，会不断从队列头部取出发送end-io中断。

### 时延模型

最核心的挑战在于计算每一个I/O请求的$$ T_{endio} $$。
（1）基础的时延模型

## nvme.h

**有关结构体**

- `struct FemuCtrl`，整个femu的全局字段。
- `struct NvmeRequest`，每个请求的相关字段。
	- `int64_t stime`：请求的开始时间戳，表示何时开始处理该请求。
	- `int64_t reqlat`：请求的时延（request latency），用于记录该请求的延迟。**`int64_t gcrt`**: 全局完成时间戳（global completion runtime）。（这个字段在femu里没有用到？）
	- `int64_t expire_time`：请求的过期时间戳，用于模拟请求超时机制（to改）。

## nand.h 和 nand.c

通过宏定义定义了闪存颗粒的时延，如`#define TLC_LOWER_PAGE_WRITE_LATENCY_NS   (820500)`。
**有关结构体**
- `struct NandFlashTiming`，维护不同flash颗粒及其不同页面的读、写、擦除和传输时延。

**有关函数**

- `init_nand_flash_timing`
该函数在`init_nand_flash`时被调用，根据所定义的宏，完成上述结构体`struct NandFlashTiming`的填充。
- `get_page_read_latency`等函数
输入flash颗粒和页面类型，从上述结构体`struct NandFlashTiming`返回对应的时延。

## timing.c

**有关函数**

- 函数`set_latency`
该函数为全局的`FemuCtrl *n`设置时延有关的字段，如`n->upg_rd_lat_ns = ...`。
- 函数`advance_channel_timestmap`
该函数根据传入的当前时间`now`，通道编号`id`，和本次操作的类型`opcode`，以及当前通道的状态`n->chnl_locks[ch]`，来更新通道编号`id`的通道下一次可以使用的时间。目前这个函数直接返回了`now`。
但根据提供的剩下代码来看，其主要思路大致描述为：（1）获取当前操作的通道可用时间。如果当前的通道是可用状态（即，`now>=n->chnl_next_avail_time[ch]`），则直接可用（即，`start_data_xfer_ts=now`）；否则会等待到可用时间。（2）更新下次操作的通道可用时间。如果当前操作是`erase`操作，通道无需做页面传输，直接可用；否则为`read`或`write`操作时，还需要等待页面传输结束（即，`n->chnl_pg_xfer_lat_ns * 2`的时间）。
（疑惑：但是为什么要乘以2，这个不太能理解，可能是出于数据传输可靠性的考虑？）
- `advance_chip_timestamp`
思路类似于上述函数`advance_channel_timestmap`，根据操作的类型得到当前操作（读、写、擦除）的时延，然后和现在芯片的可用时间`n->chip_next_avail_time[lunid]`共同更新下一次芯片的可用时间。
注意：
- 函数`advance_channel_timestmap`和 `advance_chip_timestamp`仅在oc12.c和oc20.c被调用了，暂不清楚为什么，不知道其他SSD怎么模拟的时延。
- 这些通道和芯片时延的更新，都只是修改了全局结构体`struct FemuCtrl`的有关字段。

## oc12.c 和 ftl.c

**有关函数**

- 函数`oc12_advance_status`
这个函数看起来就是oc12的时延模型函数。mark一下。看起来是根据操作类型设置了`req->expire_time`。
- 函数 `ssd_advance_status`
这个函数看起来是bbssd的时延模型函数。

## nvme-io.c

**有关函数**

- 函数`nvme_process_sq_io`
该函数初始化一个`NvmeRequest *req`，这其中包括这个`req`的`cmd_opcode`、`stime`和`expire_time`等字段，后两个时间都为现在的qemu时间。
- 函数`cmp_pri`、`get_pri`和`set_pri`
从这几个函数可以看出，在队列的维护中，以`expire_time`字段作为请求的优先级。结束时间越大，优先级越高？（有点怪，不确定，再看看）
- 函数`nvme_process_cq_cpl`
这个函数负责时延模拟？
- [ ] 究竟在哪里进行的时延delay？
应该会借助`req->expire_time`进行时延设置。

## Reference

- <a href="https://haslab.org/2021/05/03/femu-nvme.html"> FEMU/nvme源码分析 </a>
- <a href="https://www.usenix.org/system/files/conference/fast18/fast18-li.pdf"> Cheap, Accurate, Scalable and Extensible Flash Emulator </a>

