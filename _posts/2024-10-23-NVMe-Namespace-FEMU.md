---
layout: post
title: NVMe Namespace and FEMU
date: 2024-10-18 21:34:00
description: learn about NVMe namespace and code in femu
tags: ssd-simulator, flash
categories: sample-posts
featured: true
images:
  slider: true
---

经过femu时延分析，成功解决了改变介质时延而ocssd性能没有发生变化的bug。然而这次遇到的问题是改变SSD内部并行数（如channel数和chip数），ocssd的性能没有发生变化。定位到具体的原因在于`psl[i] = ns->start_block + (ppa << lbads);`，和NVMe namespace有关。

## 基本概念

**概念**。SATA SSD的一个闪存空间只对应一个逻辑空间。在NVMe中，一个闪存空间可以对应多个逻辑空间。每一个逻辑空间就是一个namespace，简称为ns。

**相关字段**。64字节NVMe命令的第4-7字节（从0开始计数）指定了要访问的ns。每个ns都有id`ns_id`和名称`ns_name`。如果将闪存空间划分为两个ns，大小分别为M个page和N个page，则其逻辑地址分别就为0~M-1和0~N-1。主机读写SSD需要同时指定ns和逻辑地址，否则会发生错误。识别命名空间数据结构包含报告命名空间大小、容量和利用率的相关字段：

- 命名空间大小 (NSZE) 字段定义了逻辑块 (LBA 0 到 n-1) 中命名空间的总大小。
- 命名空间容量 (NCAP) 字段定义了在任何时间点可以分配的最大逻辑块数。
- 命名空间利用率 (NUSE) 字段定义当前在命名空间中分配的逻辑块数。

**表现形式**。ns是由主机创建和管理的，在默认情况下，NVMe SSD 上的命名空间大小等于制造商确定的 LBA 大小。每个创建好的ns，表现为`/dev/`下的一个独立的块设备，在主机看来是两个独立的块设备（如/dev/nvme0n1 表示正在查看控制器#0的ns#1）。每个NS是独立的，可以用完全不同的参数配置。例如逻辑块大小等。

**共享与私有ns**。一个命名空间可以附加到两个或多个控制器，称为共享命名空间。相反，一个命名空间只能附加到一个控制器，称为私有命名空间。两者都由主机决定。

<div class="row mt-3">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.liquid loading="eager" path="assets/img/posts/nvme/ns-controller.png" title="honkai" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption">
    共享与私有命名空间
</div>


## FEMU有关代码

```c
#define NVME_ID_NS_NSFEAT_THIN(nsfeat)      ((nsfeat & 0x1))
#define NVME_ID_NS_FLBAS_EXTENDED(flbas)    ((flbas >> 4) & 0x1)
#define NVME_ID_NS_FLBAS_INDEX(flbas)       ((flbas & 0xf))
#define NVME_ID_NS_MC_SEPARATE(mc)          ((mc >> 1) & 0x1)
#define NVME_ID_NS_MC_EXTENDED(mc)          ((mc & 0x1))
#define NVME_ID_NS_DPC_LAST_EIGHT(dpc)      ((dpc >> 4) & 0x1)
#define NVME_ID_NS_DPC_FIRST_EIGHT(dpc)     ((dpc >> 3) & 0x1)
#define NVME_ID_NS_DPC_TYPE_3(dpc)          ((dpc >> 2) & 0x1)
#define NVME_ID_NS_DPC_TYPE_2(dpc)          ((dpc >> 1) & 0x1)
#define NVME_ID_NS_DPC_TYPE_1(dpc)          ((dpc & 0x1))
#define NVME_ID_NS_DPC_TYPE_MASK            0x7
```

```c
#define NVME_ID_NS_LBADS(ns) \
    ((ns)->id_ns.lbaf[NVME_ID_NS_FLBAS_INDEX((ns)->id_ns.flbas)].lbads)

#define NVME_ID_NS_LBADS_BYTES(ns) (1 << NVME_ID_NS_LBADS(ns))

#define NVME_ID_NS_MS(ns) \
    le16_to_cpu(((ns)->id_ns.lbaf[NVME_ID_NS_FLBAS_INDEX((ns)->id_ns.flbas)].ms))

#define NVME_ID_NS_LBAF_DS(ns, lba_index) (ns->id_ns.lbaf[lba_index].lbads)
#define NVME_ID_NS_LBAF_MS(ns, lba_index) (ns->id_ns.lbaf[lba_index].ms)
```

```c
typedef struct NvmeRangeType {
    uint8_t     type;
    uint8_t     attributes;
    uint8_t     rsvd2[14];
    uint64_t    slba;
    uint64_t    nlb;
    uint8_t     guid[16];
    uint8_t     rsvd48[16];
} NvmeRangeType;
```

```c
typedef struct NvmeLBAF {
    uint16_t    ms;
    uint8_t     lbads;
    uint8_t     rp;
} NvmeLBAF;
```

```c
typedef struct NvmeIdNs {
    uint64_t    nsze;
    uint64_t    ncap;
    uint64_t    nuse;
    uint8_t     nsfeat;
    uint8_t     nlbaf;
    uint8_t     flbas;
    uint8_t     mc;
    uint8_t     dpc;
    uint8_t     dps;
    uint8_t     nmic;
    uint8_t     rescap;
    uint8_t     fpi;
    uint8_t     dlfeat;
    uint16_t    nawun;
    uint16_t    nawupf;
    uint16_t    nacwu;
    uint16_t    nabsn;
    uint16_t    nabo;
    uint16_t    nabspf;
    uint16_t    noiob;
    uint8_t     nvmcap[16];
    uint16_t    npwg;
    uint16_t    npwa;
    uint16_t    npdg;
    uint16_t    npda;
    uint16_t    nows;
    uint8_t     rsvd74[30];
    uint8_t     nguid[16];
    uint64_t    eui64;
    NvmeLBAF    lbaf[16];
    uint8_t     rsvd192[192];
    uint8_t     vs[3712];
} NvmeIdNs;
```

```c
typedef struct NvmeNamespace {
    struct FemuCtrl *ctrl;
    NvmeIdNs        id_ns;
    NvmeRangeType   lba_range[64];
    unsigned long   *util;
    unsigned long   *uncorrectable;
    uint32_t        id;
    uint64_t        size; /* Coperd: for ZNS, FIXME */
    uint64_t        ns_blks;
    uint64_t        start_block;
    uint64_t        meta_start_offset;
    uint64_t        tbl_dsk_start_offset;
    uint32_t        tbl_entries;
    uint64_t        *tbl;
    Oc12Bbt   **bbtbl;
    /* Coperd: OC20 */
    struct {
        uint64_t begin;
        uint64_t predef;
        uint64_t data;
        uint64_t meta;
    } blk;
    void *state;
} NvmeNamespace;
```

## 参考资料

- <a href="https://nvmexpress.org/resource/nvme-namespaces/"> NVMe Namespaces | NVM EXPRESS</a>
-  <a href="https://www.ibm.com/docs/en/linux-on-systems?topic=nvme-namespaces"> NVMe Namespaces | IBM</a>
- https://www.snia.org/sites/default/files/SDCEMEA/2020/4%20-%20Or%20Lapid%20Micron%20-%20Understanding%20NVMe%20namespaces%20-%20Final.pdf
- https://www.youtube.com/watch?v=7MYw-0qfpH8