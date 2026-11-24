# BF16 直接贪心采样 / Native BF16 Greedy Sampling

实验性 vLLM-HUST Engine MOD。它在符合条件的纯贪心 MTP 请求中，直接对 BF16 全词表分数按行求一次最大值，再按索引取目标和补位 token ID。冻结的拒绝采样逻辑继续工作。带额外采样约束、要求 logprobs 或超出补丁准入条件的请求使用原路径。

An experimental vLLM-HUST Engine MOD for eligible all-greedy MTP requests. It computes one row-wise argmax on BF16 full-vocabulary scores, then selects the target and bonus token IDs. The original rejection sampler remains in use. Requests outside the guard use the frozen path.

## 测量 / Measurements

Qwen3.5-35B-A3B，BF16，双 Ascend 910B2 TP2，R10 2026.11.21.10，MTP2，FULL 图。两轮是分开计量的开发对照，每批并发 10。

| MMLU-Pro | 输出吞吐 / Throughput | P95 每 token 耗时 / TPOT | 答对 / Correct |
| --- | ---: | ---: | ---: |
| 前 10 题 / First 10 cases | +6.08% | −4.23% | 8 → 9 |
| 剩余 190 题 / Remaining 190 cases | −0.45% | −2.08% | 141 → 139 |

190 题候选组少生成 2.73% 的 token，整批快 31.12 秒。P95 TPOT 的改善在扩测中仍可见，吞吐和正确率未同步提升。此条目保留为实验 MOD，尚未进入冻结引擎栈。

On the 190-case expansion the candidate generated 2.73% fewer tokens and completed 31.12 seconds sooner. P95 TPOT decreased while throughput and accuracy were slightly lower. Qualification for a frozen engine remains pending.

[复核摘要 / Audited evidence](evidence/summary.json) · [vLLM-HUST 插件页 / MOD catalog](https://vllm-hust.sage.org.ai/plugins.html#greedy-bf16-native)

## v2 同卡复核 / v2 same-device evaluation

BF16 index-select v2 对照冻结 R10 后观察到收益不一致，暂缓集成 R11。MMLU-Pro 200 题输出吞吐
+1.88%，平均首字时延 +5.83%，答对 149→147。4K／16K 闭环并发 8 的吞吐分别变化 +0.54%／+0.01%。

The BF16 index-select v2 experiment had mixed results against frozen R10 on the same devices.
R11 integration is deferred. The report preserves fixed-five measurements, request data, and open evidence gaps.

[v2 实测、逐请求指标与验收说明 / v2 evidence](https://github.com/vLLM-HUST/vllm-hust-benchmark/tree/main/reports/greedy-bf16-v2-20261124)

## 准备覆盖件 / Build the overlay

从已经核验的 [R10 发行包](https://pypi.org/project/vllm-hust-engine/2026.11.21.10/) 部署中定位 `runtime/ascend/vllm_ascend/sample/rejection_sampler.py`。用 Python 3.10+ 和 Git 在独立目录生成候选文件。文件摘要见 [MOD 清单](mod.json)。

```sh
mkdir -p overlay
python tools/build_overlay.py /path/to/r10/sdk/runtime/ascend/vllm_ascend/sample/rejection_sampler.py overlay/rejection_sampler.py
```

工具核验底座、补丁和候选输出的 SHA-256，且只创建新文件。实测在通过原版 R10 准入后、worker 导入采样器前，于独立挂载命名空间只读挂载此覆盖件。两个 TP rank 在正式计时前都必须出现清单中的 BF16 标记。退出该隔离服务即可恢复原采样器。当前交付方式为源码覆盖件，适用版本由摘要锁定。

Use the R10 guard to admit the original runtime before mounting the generated file read-only in a private mount namespace, before worker imports. Confirm the BF16 marker on both TP ranks. Stopping the isolated service restores the original sampler. The distributed patch is pinned to the tested R10 source hash.

```sh
python -m unittest discover -s tests -v
```

底层采样器来自 [vLLM Ascend](https://github.com/vllm-project/vllm-ascend/blob/v0.30.0/vllm_ascend/sample/rejection_sampler.py#L171-L201)。本仓库维护 vLLM-HUST 的这一实验增量。

## 维护人 / Maintainer

暂任维护人 **张书豪 / Shuhao Zhang** ([@ShuhaoZhangTony](https://github.com/ShuhaoZhangTony))。

The [Apache 2.0 license](LICENSE) applies. See [NOTICE](NOTICE) for upstream attribution.