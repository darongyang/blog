---
layout: post
title: "Scanning OSDI'24 | FairyWREN: A Sustainable Cache for Emerging Write-Read-Erase Flash Interfaces"
date: 2024-11-03 21:34:00
description: Fairywren apploy flash-cache on zns to reduce device WA and carbon emission
tags: flash-cache, osdi, scanning, paper
categories: sample-posts
giscus_comments: true
images:
  slider: true
---

---

发现CMU的flash cache三部曲（cachelib->kangaroo->fairywren）都发在osdi/sosp上，工作的连续性还是让我深感震惊和佩服 :-)

上一次的分享，我讨论了云存储中的闪存缓存。今天，我将继续围绕闪存缓存的主题，但这次关注的是数据中心中的闪存缓存。我今天要分享的这篇论文名为《FairyWREN》，是由卡内基梅隆大学（CMU）团队和微软公司合作，发表在今年的计算机系统顶会 `OSDI` 上。这篇论文提出了一种用于新兴写-读-擦除闪存接口的可持续缓存方案。

我的分享将从以下几个方面展开：背景、动机、设计、测试以及总结。

<hr>


## 1 背景

近年来，碳排放和碳减排问题越来越受到关注。数据中心的碳排放占据了全球总碳排放中的重要份额。根据论文的数据，预计到2050年，数据中心的碳排放将占全球总碳排放的33%以上。为了应对这一挑战，像亚马逊、谷歌、Meta、微软等大公司都在积极寻求实现碳的净零排放。根据《2030数据中心白皮书》，零碳节能已经成为未来数据中心的一个重要目标。

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/carbon.png" title="" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    数据中心碳排放问题
</div>

借用作者在OSDI演讲中使用的一张图，我们可以看到，数据中心的碳排放主要分为两类：运营碳排放和隐含碳排放。

- `运营碳排放`相对容易控制，比如通过使用太阳能、风能等可再生能源。
- 然而，`隐含碳排放`则相对较难，逐渐占据了主导地位，达到了80%以上。隐含碳排放主要来源于数据中心基础设施的生产、运输、功耗和最终报废，根本原因在于硬件设备的一次生命周期。解决隐含碳排放问题的关键在于延长硬件设备的寿命，或者使用更低功耗的硬件。

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/two-carbon.png" title="" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    两种碳排放问题
</div>

了解了数据中心的碳减排后，我们再来看数据中心的存储体系。存储是数据中心的核心任务之一。现在主流的存储器件主要是几类：HDD，俗称的机械硬盘。SSD，俗称的固态硬盘，因其基于闪存介质，又叫做闪存存储。而DRAM就是常说的内存。不同层级的存储器件，其速度和成本不同。通常来说，如表中所示，内存DRAM的成本大于固态硬盘SSD，大于机械硬盘HDD，均差在一个数量级。在大规模的数据中心中，缓存不会全部使用DRAM，存储也不会全部使用SSD，而是通常采用一种折衷的存储方案。中间的结构被称为“闪存缓存”，它连接了主存和二级存储。

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/storage-method.png" title="" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    数据中心的“闪存缓存”存储架构
</div>

<hr>


## 2 动机

在动机上。使用闪存缓存有一个很好的优势：碳减排。内存和存储通常占据服务器碳排放的46%和40%。相比用DRAM做缓存，闪存缓存具备更低的功耗，能够减少高达12x的隐含碳排放。此外，近年来，闪存技术也在朝着更高密度的发展。一个存储单元从原来只能存储1比特，也就是SLC，发展到现在能够存储4比特，也就是QLC。相同硅片上能够存放更多比特，进一步降低生产成本，减少隐含碳排放。

目前，数据中心通过延长服务器的使用寿命来减少隐含碳排放。这相对容易达到，微软和meta等公司已经实施。但与之相比，闪存设备则相对困难，其具备非常有限的写入寿命。随着闪存密度的增加，其使用寿命进一步下降。要想达到6年写入寿命，只能限制每日的写入量非常小。从右图可以看到，纵向看不同颜色的线，使用寿命越长带来的碳排放和成本的模型值越低。从横向看不同的介质，随着存储介质密度的增加，闪存设备每日写入量的限制更加严格。

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/lifetime.png" title="" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    不同生命周期的闪存的碳排放和成本模型
</div>

然而，与每日写入量的严格限制相违背的是，假设不加以精心设计，闪存设备上会存在特别严重的写入放大。这是闪存设备的常见问题，体现为写有效数据时，会重复写入很多额外的数据。分析其主要原因包括两种：

- 第一种是`应用级写入放大`。在闪存中，数据通常按写入单元（例如64KB）进行存储。如果只想写入少量数据（例如100字节），那么就会先读取64KB的页面，修改其中的100字节，然后重新写入64KB的页面，导致最多640倍的写入放大。
- 第二种是`设备级写入放大`。当闪存存储空间满时，设备会进行垃圾回收，将有效数据聚集到一起，然后擦除原来的擦除单元。由于擦除单元的大小通常是GB级别，而写入单元只有64KB，导致有效数据的碎片，要频繁搬迁。搬迁相同的数据造成了设备级的写入放大。

可见如果没有合理的设计，闪存设备将面临严重的写入放大问题，这也是本篇论文所聚焦的核心问题之一。

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/app-wa.png" title="" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    应用级写入放大
</div>


<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/device-wa.png" title="" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    设备级写入放大
</div>


基于前面的分析，作者提出了设计可持续、低碳排放闪存缓存的三个核心要点：

- 首先，要减少无用的闲置空间，因为闲置空间会直接提高隐含碳成本；
- 其次，需要尽可能减少DRAM的使用，从而降低能耗；
- 最后，要尽量降低写入放大，以减缓设备的磨损速度。

与传统的DRAM缓存和键值存储相比，闪存缓存的设计思路更为复杂。DRAM缓存无需考虑寿命问题，而键值存储则缺乏快速删除的能力，这些都使得它们无法直接应用于闪存缓存的设计。

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/works.png" title="" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    三种闪存缓存方案
</div>

在优化闪存缓存方面，已有多项重要研究成果，且均发表在计算机系统领域的顶级会议上，如OSDI和SOSP。  第一个典型的方案是基于日志结构的闪存缓存。这种方法的核心原理是对缓存对象进行顺序的追加写，同时为每个对象建立一个对应的DRAM索引。顺序写的好处在于能够解决写入放大的问题。然而，当缓存的对象非常小时，DRAM索引的开销会变得极为庞大。例如，要缓存2TB的100字节对象，所需的DRAM索引高达75GB。

第二个是，发表在OSDI'20上的CacheLib。CacheLib采用了组相联缓存的设计，利用哈希函数替换掉了原来的DRAM索引，将每个对象映射到指定的唯一集合内，当集合写满了以后就进行缓存的替换。这样的好处是极大的降低了DRAM索引，但缺点在于带来了小对象的随机写，每次写入一个100B的小对象，都会带来几十倍到几百倍的写入放大。

第三个是，发表在SOSP'21年的最佳论文Kangaroo。Kangaroo结合了日志结构和组相联缓存的优点，提出了一种分层架构设计。具体而言，它在写入小对象时不急于立即进行哈希操作，而是先通过顺序写实现日志化缓存，随后再以集合为单位执行哈希操作。这种设计在减少应用级写入放大和DRAM索引方面取得了显著效果。然而，Kangaroo的层次设计虽然缓解了小数据与4KB写入单元的失配问题，但4KB写入单元与GB级别擦除单元的失配依然存在。这种失配仍然会导致设备级写入放大的问题。

设备级写入放大的根本原因在于传统的LBAD接口效率的低下。LBAD接口最初设计是为了简化从机械硬盘到固态硬盘的过渡，它屏蔽了设备的物理层细节，只暴露逻辑层。像Kangaroo这样的设计，其所有缓存操作，包括缓存的驱逐和替换，都基于逻辑层完成，而设备的垃圾回收则是完全自主的。这种逻辑与物理层的隔离带来了一个潜在问题。

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/LBAD-GC.png" title="architecture" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    LBAD接口会执行上层透明的垃圾回收
</div>

可以考虑一种较坏的情况：例如，设备刚刚完成一个有效数据块的搬迁，但随后该数据却因缓存替换而失效，从而导致一次无意义的写入。对于密集覆写的缓存场景，这一问题尤为突出。

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/LBAD-rewrite.png" title="architecture" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    透明垃圾回收的块随后会被重写
</div>

近年来，新兴的WREN接口（如ZNS、FDP等设备）为解决这一问题提供了新的机遇。WREN接口允许上层控制所有的写入操作，包括垃圾回收。如右图所示，这种新接口能够显著提升写入的可控性。作者将这种接口进行了规范化定义：第一，包含三种WREN操作，即写入、读取和擦除；第二，同时要求擦除操作必须以整块为单位，并由上层完全控制；此外，设备还需支持多个活跃的擦除单元。基于这一规范化定义，作者在软件层面设计了对应的闪存缓存架构。


通过硬件和软件的协同优化，FairyWREN成功实现了可持续闪存缓存的所有设计目标。

<hr>


## 3 实现

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/architecture.png" title="architecture" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    FairyWren系统结构
</div>

在设计上，FairyWREN采用了一种分层的架构。具体而言，它由两个主要模块组成：LOC模块和SOC模块。

- 第一个是`LOC模块`，用于缓存大于2KB的大对象，初步实现大小对象的分离。LOC通过日志结构实现顺序写入，并在DRAM中建立对象索引。由于对象较大，这个内存开销是可控的。这里的一个关键设计是，为了适配新接口的特性，FairyWREN将缓存段的大小对齐为一个可控的擦除单元。它的缓存插入和缓存查询都较为直接。为了设备级写入放大，本篇工作额外引入了缓存替换逻辑，后面一起介绍。
- 第二个是`SOC模块`，用于缓存小于2KB的小对象。小对象不能够采用原先的设计，因为内存开销会很大。SOC做了分层设计：包括DRAM、少量对象日志结构缓存、大量的集合日志结构缓存。缓存插入会优先插入到高层，再依次驱逐到低层。这里的一个关键设计是，同样为了适配新接口的特性，FairyWREN实现组相连缓存的变体，将Set的随机写变成了顺序追加，同时为每个Set建立内存索引（即集合日志结构缓存）。但这也带来了更多的内存索引开销，作者后续对此进行了相应设计。作者同样对SOC模块额外引入了缓存替换逻辑。

作者`最核心的贡献`在于，将传统闪存缓存的替换逻辑、设备的垃圾回收逻辑，原本分割的两者结合在一起，避免了设备层级进行无效的垃圾回收。首先，对于LOC模块，由于其是单层、顺序追加写以及对齐的设计。缓存替换只发生垃圾回收时，只需要通过LRU等方式擦除整个擦除单元即可。而SOC模块，是双层、非对齐的设计，这是论文设计的难点，也是关键点。

SOC采用了嵌套打包的算法，对于双层结构，各自空间满了之后，都会进行垃圾回收。FairyWREN从中选出一个擦除单元进行回收。此处的垃圾回收，并不是传统设备上无效的迁移。相反，闪存缓存会对回收的单元进行分析，选出自己认为有用的Set进行迁移。具体是如何选取有用的Set的？FairyWREN会将EU进行散列，恢复出Set结构。然后会检索上层结构得出哪些Set是需要回收，哪些Set需要进行重组。迁移完上述有用的Set后，FairyWREN擦除原来的单元。总结是，闪存缓存也可以控制垃圾回收，将其缓存替换相结合，避免了无效重复写。

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/nest-pack.png" title="architecture" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    SOC的nest嵌套打包算法：SOC的垃圾回收和驱逐流程
</div>

进行前面的嵌套打包时，有可能只回收一个对象，还是会带来整个Set的写入。我们把经常访问或经常写的特性，叫做热。对此FairyWREN将Set进行了冷热划分，同时将对象也进行了冷热划分。FairyWREN识别出热对象后，将其放到冷SubSet中。这样一来，只需要一直更新热SubSet即可。当然，冷热子集的对象的冷热程度会随插入而发生改变，所以需要定期进行冷热重组。


<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/hot-cold-split.png" title="hot-cold-split" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    冷热对象分离
</div>

第三个设计，前面的设计带来了Set的内存索引，而Set的冷热划分，进一步增大了这个索引。如何控制好索引开销，是一个关键的问题。FairyWREN通过切片、共享和双缓冲的方式缓解这个问题。切片散列的方式可以降低索引位数。然而，不可能为每个切片分配一个擦除单元（活跃擦除单元数是有限的）。FairyWREN引入了共享擦除单元的设计。但共享会导致不同切片写满缓冲区的速度不一样。一旦发生写满，就要进行落盘，这会导致写入闪存时的碎片化的问题。FairyWREN进一步引入了双缓冲区的方式，让快的写满后等一下慢的，缓解了这一问题。最终DRAM开销相比SOTA的额外DRAM开销控制在19%以内。

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/dram-opt.png" title="hot-cold-split" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    双缓冲区解决碎片化问题
</div>

<hr>


## 4 测试

在测试上，测试环境配置中，作者基于CacheLib、使用模拟和真实的ZNS设备，基于Meta和推特的Trace进行，并对SSD寿命和碳排放进行了建模。

对比对象包括：

- 理想的写入
- 日志结构缓存
- SOTA Kangaroo
- Kangaroo简单移植到ZNS的版本，也就是不做额外设计。

从总体的碳排放结果中，可以看到FairyWREN对比SOTA Kangaroo总体排放量减少21.2%，最核心原因在于FairyWREN的闪存碳排放最少。

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/result1.png" title="" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    总体的碳排放对比
</div>

在磨损速度和性能的测试上，FairyWREN对比SOTA Kangaroo减少了12.5x的写入放大，也就是磨损速度。性能均比Kangaroo要好。并且对于缓存而言，这些优势并没有以牺牲缓存命中率为代价。

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/result2.png" title="" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    磨损速度和性能测试
</div>

作者进一步研究了不同命中率下的影响，对比了直接将Kangaroo搬到新接口的方案，发现FairyWREN接近理想情况，且直接将Kangaroo搬到新接口的优化效果不大。


<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/result4.png" title="" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    磨损速度和性能测试
</div>



作者在各种高密度闪存上进行测试分析，认为只有FairyWREN能够运用到高密度闪存QLC和PLC上。具体是哪些技术点带来了这些优势？作者进一步进行分解测试，可以看到嵌套打包和冷热分离两个技术均贡献了多倍的优化。

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/fairywren/result3.png" title="" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    分解测试
</div>

<hr>


## 5 总结

以上是论文的全部内容。下面我对这篇论文进行简单小结.

这篇论文`主要背景`是数据中心的碳排放问题，存储器件的碳排放贡献很大。

然而`问题`是：（1）高密度闪存带来低碳的契机，但其寿命受到严峻挑战。（2）传统的LBAD接口会带来两级写入放大加剧寿命磨损。（3）现有的缓存方案，并不符合可持续使用的要求。

`机遇`是近年来出现了新的WREN接口，围绕其新硬件特性作者对闪存缓存进行了软件设计，最终解决上述的问题。

总的来说，在软件设计上，作者的`方案`是：

- 提出适配到新接口的设计架构
- 通过嵌套打包算法统一垃圾回收和缓存写入
- 进一步作者还实现了冷热对象分离和DRAM开销优化

最终系统整体上表现最佳。

本文亮眼之处在于其总结性的写作方法、让人眼前一亮的新背景、以及扎实的建模和实验。作者团体在本次OSDI投稿前，就已经在HotCarbon'24上发表过有关存储器件碳排放建模分析的文章，功底很扎实。

论其不足之处，我认为是过于简单的设计，对工作独到之处没有明确，需要读者对比阅读和总结。

最后：Flash Cache会面临小对象存储的问题，但感觉能优化点已经到头了，从2021年Kangaroo到2024年FairyWREN，还是因为又新硬件接口ZNS才又激起一点波浪。

<hr>

## reference

- <a href="https://www.usenix.org/conference/osdi24/presentation/mcallister"> FairyWREN | OSDI'24 </a>
- <a href="https://saramcallister.github.io/files/2024-osdi-mcallister-slides.pdf"> FairyWREN Presentation Slides</a>
- <a href="https://mp.weixin.qq.com/s/0g1jBn9SdE4QwygKx2qwQQ">【论文解读】数据中心节能减排：可持续的闪存缓存设计 FairyWREN (OSDI'24) </a>
- <a href="https://www.zhihu.com/question/649626302/answer/3596509565"> 2024年操作系统设计与实现研讨会（OSDI）有哪些值得关注的文章？--FairyWREN </a>
- <a href="https://zhuanlan.zhihu.com/p/708037149"> OSDI 2024 论文评述 Day 3 Session 9: Data Management | IPADS-SYS </a>