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

上一次的分享，我讨论了云存储中的闪存缓存。今天，我将继续围绕闪存缓存的主题，但这次关注的是数据中心中的闪存缓存。我今天要分享的这篇论文名为《FairyWREN》，是由卡内基梅隆大学（CMU）团队和微软公司合作，发表在今年的计算机系统顶会 _OSDI_ 上。这篇论文提出了一种用于新兴写-读-擦除闪存接口的可持续缓存方案。

我的分享将从以下几个方面展开：背景、动机、设计、测试以及总结。

## 背景

近年来，碳排放和碳减排问题越来越受到关注。数据中心的碳排放占据了全球总碳排放中的重要份额。根据论文的数据，预计到2050年，数据中心的碳排放将占全球总碳排放的33%以上。为了应对这一挑战，像亚马逊、谷歌、Meta、微软等大公司都在积极寻求实现碳的净零排放。根据《2030数据中心白皮书》，零碳节能已经成为未来数据中心的一个重要目标。

借用作者在OSDI演讲中使用的一张图，我们可以看到，数据中心的碳排放主要分为两类：运营碳排放和隐含碳排放。运营碳排放相对容易控制，比如通过使用太阳能、风能等可再生能源。然而，隐含碳排放则相对较难，逐渐占据了主导地位，达到了80%以上。隐含碳排放主要来源于数据中心基础设施的生产、运输、功耗和最终报废，根本原因在于硬件设备的生命周期。

了解了数据中心的碳减排后，我们再来看数据中心的存储系统。存储是数据中心的核心任务之一。现在主流的存储器件主要是两类：HDD，俗称的机械硬盘。SSD，俗称的固态硬盘，又叫做闪存存储，因为基于闪存介质。内存则通常使用DRAM。不同层级的存储器件，其速度和成本不同。通常来说，如表中所示，内存DRAM的成本大于固态硬盘SSD，大于机械硬盘HDD，均差一个数量级。在大规模的数据中心中，缓存不会全部使用DRAM，存储也不会全部使用SSD，而是采用折衷的闪存缓存的存储体系。中间的结构被称为“闪存缓存”，它连接了主存和二级存储。

## 动机

在动机上。使用闪存缓存有一个很好的优势：碳减排。内存和存储通常占据服务器碳排放的46%和40%。相比用DRAM做缓存，闪存缓存具备更低的功耗，能够减少高达12x的隐含碳排放。此外，近年来，此外，闪存技术近几年也在朝着更高密度的发展。一个存储单元从原来只能存储1比特，也就是SLC，发展到现在能够存储4比特，也就是QLC。相同硅片上能够存放更多比特，进一步降低生产成本，减少隐含碳排放。

目前，数据中心通过延长服务器的使用寿命来减少隐含碳排放。这容易达到，微软和meta等公司已经实施。但与之相比，闪存设备则相对困难，其具备非常有限的写入寿命。随着闪存密度的增加，其使用寿命进一步下降。为了达到6年写入寿命，只能限制每日写入量很小。从右图可以看到，纵向看不同颜色的线，使用寿命越长带来的碳排放和成本的模型值越低。从横向看不同的介质，随着存储介质密度的增加，闪存设备每日写入量的限制更加严格。

然而，与每日写入量的严格要求相违背的是，假设不加以精心设计，闪存设备上会存在特别大的写入放大。这是闪存设备的常见问题，体现为写有效数据时，会重复写入很多额外的数据。主要分析其原因包括两种：第一种是应用级写入放大。在闪存中，数据通常按写入单元（例如64KB）进行存储。如果只写入少量数据（例如100字节），那么就会先读取64KB的页面，修改其中的100字节，然后重新写入64KB的页面，导致最多640倍的写入放大。第二种是设备级写入放大。当闪存存储空间满时，设备会进行垃圾回收，将有效数据聚集到一起，然后擦除原来的擦除单元。由于擦除单元的大小通常是GB级别，而写入单元只有64KB，导致有效数据的碎片需要频繁搬迁，进一步加剧了写入放大。如果没有合理的设计，闪存设备将面临严重的写入放大问题，这也是本篇论文所聚焦的核心问题之一。


最新事情有点多，没时间更新，请先参考我的论文解读PPT：<a href="https://darongyang.github.io/blog/assets/pdf/FairyWREN-v1.pdf"> FairyWREN-Reading-PPT </a>

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
- **讨论**。这个方法能带来接近一半的写放大优化。eg: n=5, Set=8KB，能实现40KB->24KB的写入量减少40%。但，也不是划分越多越好。而WREN只支持有限的EU（10个）。FairyWREN使用4个EU。此外，冷热分离会是的cache命中率下降，识别未必是准确的。


### 3.4 DRAM使用优化

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/dram-reduce.png" title="hot-cold-split" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    双缓冲区解决碎片化问题
</div>


- **设计：日志结构切片**。FwLog的object，FwSet的Set都是按照日志结构存储，分别需要object和Set的索引，DRAM开销很大。对日志结构存储空间进行 $2^n$ 切片可以减少n比特索引。（FwLog划分64份，FwSet划分8份）
- **朴素方法**。一种朴素的思路是一个分片用一个EU/segment，然而EU数有限。不切实际。
- **设计：共享EU/segment和碎片化问题**。所有切片共用一个sgement/EU，将DRAM中的segment分成 $2^n$ 份切片区域。各个切片将对应的区域写满后，再一次全部写到EU中。然而这会导致：部分区域可能提前写满，而其他区域没写满时就得写回EU，导致碎片化问题。
- **设计：双缓冲区**。FairyWREN采用了双缓冲区来延缓这个问题，写的快的区域，可以写入到副本缓冲区中的新区域，起到一定的“快”等”慢“的作用。等主缓冲区尽可能写满后，就写回到EU中。（效果很好，将碎片化问题限制在了1%）
- **设计：更大的Set**。此外，FairyWREN还通过增大 Set大小来减小 FwSet 索引。（作者讨论了更大的Set不会带来写放大可控，即5%）

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/dram-result.png" title="hot-cold-split" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    DRAM开销定量对比
</div>

最后，FairyWREN 使用的 DRAM 仅比 Kangaroo 多 19%，但后续会看到比 Kangaroo带来了12.5x写入量的减少。


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