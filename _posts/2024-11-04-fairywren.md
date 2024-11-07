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

正在阅读中，后续推送一下......

## 2 研究动机

### 2.4 关键动机：LBAD接口的DLWA（GC的写放大）

Kangaroo基于传统的LBAD接口。LBAD接口屏蔽了物理层，只暴露逻辑层。Kangaroo的缓存驱逐/替换操作基于逻辑层，LBAD的垃圾回收操作基于物理层，两者互不知情。那么就会带来：GC经常会重写一些无效的数据。表现为：GC刚搬迁完，这个数据就被替换而无效了。对于密集覆写的闪存缓存来说，这个问题尤为显著。因此，作者认为垃圾回收是缓存替换的一个机会。

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/LBAD-GC.png" title="architecture" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    LBAD接口会执行上层透明的垃圾回收
</div>

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/LBAD-rewrite.png" title="architecture" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    透明垃圾回收的块随后会被重写
</div>



## 3 设计实现

（想把最头大的这部分先捋清楚...）

**Key insight**：将垃圾回收和缓存准入进行统一，无论在线写入还是垃圾回收都能够进行对象准入。（换句话说，就是借助WREN让垃圾回收的时候做到object attention，主动判断哪些对象要重写/回收，避免像LBAD那样无效回收）

### 3.1 系统结构

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/architecture.png" title="architecture" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    FairyWren系统结构
</div>

- LOC：缓存大对象（>2KB）
	- DRAM：EU大小的segment buffer + 大对象索引
	- LOC：采用日志化结构缓存，执行大的顺序写。适应到WREN很简单，segment大小定为一个EU即可。由于对象较大，其DRAM开销较小。
	- 两种缓存操作：（1）**插入**。先插入DRAM并建立索引，segment满了一起写闪存。当插入发生替换时，采用GC相结合的设计，见3.2。（2）**查询**。查询查找object的key对应的地址，然后从闪存读取。
- SOC：缓存小对象
	- DRAM：FwLog的segment buffer + FwLog的小对象索引 + FwSet的set索引
	- FwLog：采用日志化结构缓存，缓冲小object以便可以高效写入FwSet。小对象索引DRAM开销大，为了保证其开销，FwLog只占SOC的5%。
	- FwSet：采用组相连缓存。对小对象进行日志化缓存会DRAM爆炸。WREN接口不支持随机写，FwSet适配到WREN中要遵循日志结构存储，将set（大于4KB）作为日志化追加的对象（关键设计）。set索引开销小。
	- 两种缓存操作：（1）**插入**。采用类似于LOC方式先插入到FwLog，如果FwLog满了，会插入到FwSet中。FwSet的插入可能会进一步导致FwSet的替换，采用GC相结合的设计，见3.2。（2）**查询**。首先采用类似于LOC方式在FwLog查询，如果找不到再hash得到对象在FwSet中对应的Set。在Set内顺序扫描找到对象。

### 3.2 垃圾回收和在线写的统一

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/nest-pack.png" title="architecture" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    nest打包方法：SOC的垃圾回收和驱逐流程
</div>

- LOC
	- 当LOC满的时候，FairyWREN进行替换。驱逐时，由于segment和EU对齐，通过LRU或FIFO移除整个segment，即EU即可，完成WA=1的擦除。
- SOC（关键设计）
	- **朴素方法**。当FwSet或FwLog满的时候，需要进行垃圾回收。FairyWREN同样将其和缓存替换相结合。一个最朴素的方法是直接将末尾的EU驱逐，但冷热对象混杂会大大降低命中率。
	- **FairyWREN的“嵌套打包”**。（1）**EU选择**。FairyWREN从FwSet和FwLog中选择一个EU进行垃圾回收。（2）**Set散列**。FairyWREN会将选中的EU的所有对象哈希散列为若干Set（如果EU在FwSet中，本身就已经是若干的Set）。（3）**Set重组**。对于这些Set，FairyWREN会检索出FwLog中位于Set的所有对象。将这些Set的对象重组为一个新的Set，其中可能会逐出不必要的对象。（4）**重写与擦除**。然后将重组的Set，重新追加写入到FwSet，并擦除上述EU。
	- **如何work**？设计的最关键在于：合并了之前两个不同的过程，实现垃圾回收和缓存写入与驱逐/替换的协作。最坏的例子（如前面2.4所介绍）：LBAD的垃圾回收刚搬迁完一个Set，然后FwLog来了一个新对象后，又要马上被重写。在LBAD中，无法实现写入合并。而FairyWREN基于上述的嵌入打包，消除了很多不必要的写入。

### 3.3 KwSet的冷热对象分离

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/hot-cold-split.png" title="hot-cold-split" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    冷热对象分离
</div>

- **动机：** 每次从FwLog插入一个对象到FwSet，都会带来整个Set的重写。
- **冷热对象分离**。（1）**Set划分**。将KwSet划分为两个SubSet，频繁更新的热SubSet和不频繁更新的冷SubSet。冷热SubSet分别处于不同的EU中。（2）**对象识别与放置**。冷热对象的识别通过RRIP算法完成。值得注意，对于闪存缓存来说，热对象要放到冷SubSet中，因为其不会频繁被“驱逐”，会常驻于KwSet中；冷对象与之相反。这样一来，每次FwLog到FwSet的散列插入对象，只需要对KwSet中的热SubSet频繁更新即可。（3）**冷热重分类**。 但不能一直插入热SubSet，因为新插入的对象可能是热对象。因此Set每进行n次（设定的阈值）嵌套打包操作后，会进行一次全SubSet的读取（包括冷和热SubSet）。Set中的对象会重新进行合并和分类，将上述热SubSet中新插入的热对象移动到冷SubSet中。
- （4）**讨论**。这个方法能带来接近一半的写放大优化。eg: n=5, Set=8KB，能实现40KB->24KB的写入量减少40%。但，也不是划分越多越好。而WREN只支持有限的EU（10个）。FairyWREN使用4个EU。此外，冷热分离会是的cache命中率下降，识别未必是准确的。


### 3.4 DRAM使用优化

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/dram-recude.png" title="hot-cold-split" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    双缓冲区解决碎片化问题
</div>

- **DRAM 需求缩减优化：** 类似于 Kangaroo，将 keyspace 根据 key 静态分成多个独立的缓存分区，以节省每个索引项的比特长度。另外，通过增大 set size 来减小 FwSet 索引。FairyWREN 的 DRAM 开销分解分析如下，总体上每缓存一个 object 平均需要 8.3 bit 元数据。


## 个人评价

- 技术写作还是很难懂的，如果之前没读过Kangaroo和CacheLib。很多细节略过，不知其所以然。
- 创新点真的太weak了，写来写去全是和kangaroo一个模子刻出来的。至少目前看起来，大小object分离、Fwlog和Fwset分层、冷热分离等等都是kangaroo提到过的。晦涩难懂又没创新。
- design开始看的真的折磨

## reference

- <a href="https://www.usenix.org/conference/osdi24/presentation/mcallister"> FairyWREN | OSDI'24 </a>
- <a href="https://saramcallister.github.io/files/2024-osdi-mcallister-slides.pdf"> FairyWREN Presentation Slides</a>
- <a href="https://mp.weixin.qq.com/s/0g1jBn9SdE4QwygKx2qwQQ">【论文解读】数据中心节能减排：可持续的闪存缓存设计 FairyWREN (OSDI'24) </a>
- <a href="https://www.zhihu.com/question/649626302/answer/3596509565"> 2024年操作系统设计与实现研讨会（OSDI）有哪些值得关注的文章？--FairyWREN </a>
- <a href="https://zhuanlan.zhihu.com/p/708037149"> OSDI 2024 论文评述 Day 3 Session 9: Data Management | IPADS-SYS </a>