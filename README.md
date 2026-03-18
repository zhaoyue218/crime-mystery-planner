# AI Crime Mystery Story Generation System

一个面向课程项目的、最小但完整的“AI 犯罪推理故事生成系统”。

这份 README 主要是给当前仓库的开发者/学生自己看的。重点不是宣传功能，而是帮助你准确理解：

- 现在的代码到底做了什么
- 各个模块之间如何连接
- 哪些部分已经接入真实 LLM
- 哪些部分仍然是模板化、启发式或尚未完全对齐

当前文档严格基于仓库里的真实代码编写，不会假设不存在的模块或能力。

---

## 1. 项目概述

### 1.1 这个项目要解决什么问题

这个项目不是单纯“让大模型写一篇侦探小说”，而是尝试把犯罪推理故事生成拆成几个明确阶段：

1. 先生成一个隐藏的案件真相
2. 再把真相转换成结构化事实
3. 再生成调查过程计划
4. 再对计划做规则校验
5. 如果计划有问题，再做局部修复
6. 最后才输出可读的故事文本

项目希望体现一种更适合课程展示的思路：

- 用结构化对象保存真相
- 用规则检查调查过程
- 用局部修补替代整段重写
- 把最终小说文本当作“结构结果的实现层”

### 1.2 当前系统的整体思路

当前代码里，系统主要围绕下面三层数据展开：

1. `CaseBible`
   - 表示隐藏真相层
   - 包含 victim、culprit、suspects、motive、method、true_timeline、evidence_items、red_herrings、culprit_evidence_chain

2. `FactTriple`
   - 表示机器可检查的事实层
   - 是从 `CaseBible` 编译出来的三元组列表

3. `PlotPlan`
   - 表示调查过程层
   - 每一步是结构化的 `PlotStep`

最后，`StoryRealizer` 再把这些内容转成 `story.txt`。

### 1.3 为什么它不是单纯文本生成

这个项目不是“输入一句 prompt，直接出小说”，原因是：

- 案件真相先保存在 `CaseBible` 里，而不是先写成长文本
- 事实被展开成 `FactTriple` 列表，而不是埋在 prose 里
- 调查过程是 `PlotPlan.steps`，每一步都有固定字段
- `validator.py` 使用的是确定性规则，不依赖 LLM 判断
- `repair_operator.py` 做的是局部修复，而不是把整案重新生成

所以它的核心不是纯叙事，而是：

**结构化生成 + 显式验证 + 局部修复 + 最终叙事实现**

---

## 2. 项目整体流程

### 2.1 从入口开始的顺序

程序入口是 [main.py](/Users/yuezhao/Documents/New%20project/main.py)。

运行：

```bash
python main.py
```

后，执行顺序如下：

1. `main.py` 解析参数
2. 创建 `CrimeMysteryPipeline`
3. `pipeline.run()` 触发整个流程
4. `CaseBibleGenerator.generate()` 生成隐藏真相
5. `FactGraphBuilder.build()` 构建事实图
6. `PlotPlanner.build_plan()` 生成调查计划
7. `PlotPlanValidator.validate()` 检查计划
8. 如果失败，`PlotPlanRepairOperator.repair()` 做修复
9. `StoryRealizer.realize()` 生成最终故事文本
10. 将结构化输出和文本输出保存到 `outputs/`

### 2.2 文字版流程图

```text
python main.py
  ->
parse_args()
  ->
CrimeMysteryPipeline(...)
  ->
pipeline.run()
  ->
CaseBibleGenerator.generate()
  ->
CaseBible
  ->
FactGraphBuilder.build(case_bible)
  ->
fact_graph
  ->
PlotPlanner.build_plan(case_bible)
  ->
initial_plot_plan
  ->
PlotPlanValidator.validate(case_bible, initial_plot_plan)
  ->
initial_report
  ->
if invalid:
    PlotPlanRepairOperator.repair(...)
    ->
    validate again
  ->
StoryRealizer.realize(case_bible, final_plot_plan)
  ->
story_text
  ->
save outputs/*.json + outputs/story.txt
```

### 2.3 用“输入 -> 中间表示 -> 校验 -> 修复 -> 输出”理解

#### 输入

当前系统的输入主要有三类：

- 命令行参数：`--output-dir`、`--seed`
- 外部设定文件：[generators/setting.txt](/Users/yuezhao/Documents/New%20project/generators/setting.txt)
- LLM backend 返回的文本

#### 中间表示

中间表示主要有三层：

1. `CaseBible`
2. `list[FactTriple]`
3. `PlotPlan`

它们分别表示：

- 真实发生了什么
- 程序可检查的事实
- 调查如何逐步接近真相

#### 校验

校验由 [validators/validator.py](/Users/yuezhao/Documents/New%20project/validators/validator.py) 完成。

它检查的不是自然语言质量，而是结构约束，比如：

- 嫌疑人数是否足够
- 证据数是否足够
- 是否有红鲱鱼
- 是否有至少两个 alibi check
- 最终 confrontation 是否引用关键证据
- plot step 时间顺序是否单调

#### 修复

修复由 [repair/repair_operator.py](/Users/yuezhao/Documents/New%20project/repair/repair_operator.py) 完成。

它不是整案重生成，而是根据失败项补：

- alibi 步骤
- interference 步骤
- red herring 步骤
- 缺失的 evidence chain
- 缺失或证据不足的 confrontation

#### 输出

输出分两类：

结构化输出：

- `case_bible.json`
- `fact_graph.json`
- `plot_plan.json`
- `validation_report.json`

文本输出：

- `story.txt`

---

## 3. 代码目录结构

```text
.
├── builders/
│   └── fact_graph_builder.py
├── generators/
│   ├── case_bible_generator.py
│   └── setting.txt
├── planners/
│   └── plot_planner.py
├── realization/
│   └── story_realizer.py
├── repair/
│   └── repair_operator.py
├── validators/
│   └── validator.py
├── outputs/
│   ├── case_bible.json
│   ├── fact_graph.json
│   ├── plot_plan.json
│   ├── validation_report.json
│   └── story.txt
├── llm_interface.py
├── main.py
├── models.py
├── pipeline.py
└── README.md
```

### [main.py](/Users/yuezhao/Documents/New%20project/main.py)

- 命令行入口
- 负责读取参数并启动 pipeline
- 不承担生成逻辑，只做 orchestration 的最外层封装

### [pipeline.py](/Users/yuezhao/Documents/New%20project/pipeline.py)

- 全项目的流程编排中心
- 串起 generation、fact building、planning、validation、repair、realization、save outputs
- 如果只想先理解全局，最适合先读这个文件

### [models.py](/Users/yuezhao/Documents/New%20project/models.py)

- 定义全系统共享的数据结构
- 这些 dataclass 就是各模块之间的“内部协议”
- 当前项目的数据流基本都是围绕这些类流转

### [llm_interface.py](/Users/yuezhao/Documents/New%20project/llm_interface.py)

- 定义 LLM 抽象接口 `LLMBackend`
- 提供两个具体 backend：
  - `MockLLMBackend`
  - `GeminiLLMBackend`
- 现在项目已经接入真实 Gemini HTTP 调用

### [generators/case_bible_generator.py](/Users/yuezhao/Documents/New%20project/generators/case_bible_generator.py)

- 负责生成隐藏真相 `CaseBible`
- 当前不再手工硬编码 victim/suspects/timeline/evidence
- 而是读取 `setting.txt`，让 LLM 返回一份 JSON blueprint，再本地解析成 dataclass

### [generators/setting.txt](/Users/yuezhao/Documents/New%20project/generators/setting.txt)

- 当前案件生成的外部约束文件
- 不是简单的 setting 名称，而是一整段“时代/风格/空间/公平推理规则”的约束说明

### [builders/fact_graph_builder.py](/Users/yuezhao/Documents/New%20project/builders/fact_graph_builder.py)

- 负责把 `CaseBible` 转成 `FactTriple` 列表
- 当前已经移除了 `confidence`
- 时间不再写死，而是根据 `true_timeline` 做规则式推断

### [planners/plot_planner.py](/Users/yuezhao/Documents/New%20project/planners/plot_planner.py)

- 负责生成 `PlotPlan`
- 当前仍然是旧模板化实现
- 它没有根据新的 `CaseBible` 动态规划，而是写死了一组旧案件的 plot steps
- 这是当前系统里最重要的未对齐点之一

### [validators/validator.py](/Users/yuezhao/Documents/New%20project/validators/validator.py)

- 负责做结构性校验
- 输入是 `CaseBible + PlotPlan`
- 输出是 `ValidationReport`
- 当前校验逻辑完全是 deterministic 的，不调用 LLM

### [repair/repair_operator.py](/Users/yuezhao/Documents/New%20project/repair/repair_operator.py)

- 在 validation 不通过时做局部修复
- 是启发式补丁，不是重新生成
- 目标是尽量把 plan 调整到满足项目要求

### [realization/story_realizer.py](/Users/yuezhao/Documents/New%20project/realization/story_realizer.py)

- 负责生成最终 `story.txt`
- 当前支持 backend 分流：
  - Mock backend：简单拼接式 realization
  - Gemini backend：把 `CaseBible + PlotPlan` 组织成 prompt 交给模型生成自然叙事

### `outputs/`

- 保存最近一次运行产生的结果
- 它们是理解系统当前行为最直观的窗口

---

## 4. 核心数据结构 / schema

这一部分只解释**当前代码里真实存在的结构**。

### 4.1 `Character`

定义在 [models.py](/Users/yuezhao/Documents/New%20project/models.py)。

字段：

- `name`
  - 人物名
  - 在所有模块中广泛使用：case bible、fact graph、plot plan、story realization

- `role`
  - 角色类型，例如 `victim`、`suspect`、`culprit`
  - `CaseBibleGenerator` 会根据 `culprit_name` 把对应 suspect 的 role 改成 `culprit`

- `description`
  - 人物简介
  - 主要在 case bible 和 story realization 中使用

- `relationship_to_victim`
  - 与受害者关系
  - 在 fact graph 中展开为 `relationship_to_victim`

- `means`
  - 作案手段或能力
  - 在 fact graph 中保留

- `motive`
  - 个体动机
  - 区别于 `CaseBible.motive` 的“全案真实动机”

- `opportunity`
  - 个体机会说明
  - fact graph 会保留，并为其推断一个时间窗口

- `alibi`
  - 不在场证明描述
  - validator 不直接检查文本内容，但 plot plan 中有专门的 `alibi_check` 步骤类型

### 4.2 `EvidenceItem`

字段：

- `evidence_id`
- `name`
- `description`
- `location_found`
- `implicated_person`
- `reliability`
- `planted`

说明：

- `reliability` 仍存在于 `EvidenceItem` 中，但已经**不再写入 `FactTriple`**
- `planted` 用来表示该证据是否是嫁祸/布置出来的

### 4.3 `TimelineEvent`

字段：

- `event_id`
- `time_marker`
- `summary`
- `participants`
- `location`
- `public`

说明：

- `true_timeline` 是整个案件的隐藏时间线
- `FactGraphBuilder` 现在会直接依赖这些事件来推断：
  - victim 时间
  - culprit 方法时间
  - 角色时间窗口

### 4.4 `RedHerring`

字段：

- `herring_id`
- `suspect_name`
- `misleading_evidence_ids`
- `explanation`

说明：

- 红鲱鱼对象不是最终小说文本，而是结构化误导线索
- validator 要求 plot plan 中必须出现 red herring arc

### 4.5 `CaseBible`

这是整个系统最核心的隐藏真相对象。

字段：

- `setting`
- `victim`
- `culprit`
- `suspects`
- `motive`
- `method`
- `true_timeline`
- `evidence_items`
- `red_herrings`
- `culprit_evidence_chain`

说明：

- `setting` 现在来自 `setting.txt`
- 其余内容主要由 `CaseBibleGenerator` 调用 Gemini 生成 JSON 再解析得到
- 后续几乎所有模块都依赖 `CaseBible`

### 4.6 `FactTriple`

字段：

- `subject`
- `relation`
- `object`
- `time`
- `source`

说明：

- 当前已删除 `confidence`
- 所以现在的 fact triple 更像“轻量、可序列化的结构化事实”
- `source` 用于区分事实来源，例如：
  - `case_bible`
  - `timeline`
  - `evidence`
  - `red_herring`

### 4.7 `PlotStep`

字段：

- `step_id`
- `phase`
- `kind`
- `title`
- `summary`
- `location`
- `participants`
- `evidence_ids`
- `reveals`
- `timeline_ref`

说明：

- `PlotStep` 仍然带有 `title`
- `StoryRealizer` 目前也仍然在使用 `title`
- 这部分与前面曾经尝试去 title 的方向不一致，但以当前仓库代码为准

### 4.8 `PlotPlan`

字段：

- `investigator`
- `steps`

说明：

- `case_title` 已删除
- 计划中只保留 investigator 和步骤列表

### 4.9 `ValidationIssue` 与 `ValidationReport`

`ValidationIssue`：

- `code`
- `message`
- `step_id`

`ValidationReport`：

- `is_valid`
- `issues`
- `metrics`

说明：

- validator 的输出不是简单布尔值，而是详细报告
- repair 会依赖 `issue.code` 决定补哪些步骤

---

## 5. 各模块详细说明

### [models.py](/Users/yuezhao/Documents/New%20project/models.py)

主要职责：

- 定义项目全部核心数据结构

输入：

- 无直接运行输入，它是被各模块 import 的 schema 定义文件

输出：

- 各 dataclass 类型

内部逻辑：

- 几乎没有业务逻辑
- 只有一个 `to_data()` 帮助把 dataclass 递归转成普通数据

依赖：

- 标准库 `dataclasses`、`typing`

被谁调用：

- 全项目几乎所有模块

在系统中的位置：

- 最底层 schema 层

### [llm_interface.py](/Users/yuezhao/Documents/New%20project/llm_interface.py)

主要职责：

- 把“如何调用语言模型”封装成统一接口

关键类：

- `LLMResponse`
- `LLMBackend`
- `MockLLMBackend`
- `GeminiLLMBackend`

输入：

- 一个 prompt 字符串

输出：

- `LLMResponse(text=...)`

内部逻辑：

- `MockLLMBackend`
  - 根据 prompt 关键词返回固定候选文本之一
  - 适合离线或演示

- `GeminiLLMBackend`
  - 用 `urllib.request` 发 POST 请求
  - 调用 Gemini 的 `generateContent`
  - 解析响应中的 `candidates[0].content.parts[*].text`

依赖：

- 标准库 `json`、`urllib`

被谁调用：

- `CaseBibleGenerator`
- `StoryRealizer`
- `pipeline.py` 负责实例化 backend

在系统中的位置：

- LLM 抽象层

当前实现说明：

- 默认已经接入真实 Gemini
- 目前 `pipeline.py` 中实际把 Gemini 传给了 `CaseBibleGenerator` 和 `StoryRealizer`
- `MockLLMBackend` 仍被实例化并保留，但当前 pipeline 默认不使用它做主流程

### [generators/case_bible_generator.py](/Users/yuezhao/Documents/New%20project/generators/case_bible_generator.py)

主要职责：

- 生成整个案件的隐藏真相对象 `CaseBible`

输入：

- `setting.txt`
- 一个 `LLMBackend`

输出：

- `CaseBible`

内部核心逻辑：

1. 读取 `setting.txt`
2. 组织 prompt，要求模型返回严格 JSON
3. 调用 `self.llm.generate(prompt)`
4. 从返回文本中提取 JSON
5. 做基础结构检查
6. 映射为：
   - `Character`
   - `TimelineEvent`
   - `EvidenceItem`
   - `RedHerring`
   - `CaseBible`

关键点：

- 现在 victim/suspects/timeline/evidence 已不是手写
- 而是 Gemini 动态生成
- 但本地会做一层 schema 解析和字段检查

当前局限：

- 只做了基础结构校验，没有做非常深的语义一致性修复
- 如果 Gemini 输出 JSON 不稳定，可能直接抛错
- `self.rng` 当前仍保留，但实际上没有参与逻辑

依赖：

- `llm_interface.py`
- `models.py`

被谁调用：

- `pipeline.py`

在系统中的位置：

- 整个系统最上游的 truth generation 层

### [builders/fact_graph_builder.py](/Users/yuezhao/Documents/New%20project/builders/fact_graph_builder.py)

主要职责：

- 把 `CaseBible` 转换为 `FactTriple` 列表

输入：

- `CaseBible`

输出：

- `list[FactTriple]`

内部核心逻辑：

1. 先把 `true_timeline` 变成内部 `_TimedEvent` 列表并按时间排序
2. 推断 victim 时间
3. 推断 method 时间
4. 为每个 suspect 推断一个和案发相关的时间窗口
5. 展开 case-level facts、suspect-level facts、timeline facts、evidence facts、red herring facts

时间推断比以前更严格的地方：

- 不再手写固定时间
- `is_victim` 的时间优先找“明确死亡”事件，而不是“发现尸体”事件
- `used_method` 的时间优先找凶手实施动作的事件
- 角色窗口会聚焦在案发附近，而不是简单取最早到最晚

名字归一化：

- 会去掉 `Lord`、`Lady`、`Sir`、`Dr` 等称谓
- 所以 `Sir Alistair Thorne` 与 `Alistair Thorne` 能匹配

当前局限：

- 时间推断仍然是规则/关键词驱动，不是真正语义理解
- 如果 timeline summary 写得非常规整之外，推断可能仍不够理想
- 如果 timeline 里出现 `N/A` 这类占位 participant，fact graph 目前仍会原样写入

依赖：

- `models.py`

被谁调用：

- `pipeline.py`

在系统中的位置：

- truth layer 到 machine-checkable facts layer 的编译层

### [planners/plot_planner.py](/Users/yuezhao/Documents/New%20project/planners/plot_planner.py)

主要职责：

- 生成结构化调查计划 `PlotPlan`

输入：

- `CaseBible`

输出：

- `PlotPlan`

内部核心逻辑：

- 当前直接返回一个写死的 17-step 计划
- 这组步骤来自旧案件模板

非常重要的现实情况：

- 这个文件**目前没有根据动态生成的 `CaseBible` 自适应**
- 它仍然写死了旧人物、旧证据和旧时间
- 因此它和当前 Gemini 版 `CaseBibleGenerator` 之间是**未完全对齐的**

这意味着：

- validator 往往会在这里报出很多 mismatch
- story realization 也可能因此和 case bible 脱节

这是当前仓库里最需要继续演进的模块。

### [validators/validator.py](/Users/yuezhao/Documents/New%20project/validators/validator.py)

主要职责：

- 对 `PlotPlan` 做确定性规则校验

输入：

- `CaseBible`
- `PlotPlan`

输出：

- `ValidationReport`

内部核心逻辑：

- 检查 suspects 数量
- 检查 evidence 数量
- 检查 step 数量
- 检查 alibi check 数量
- 检查是否存在 red herring
- 检查是否存在 interference
- 检查 culprit evidence chain 是否被 plot 引用
- 检查 confrontation 是否存在且是否引用关键证据
- 检查 culprit 是否在足够多步骤中被支持
- 检查 step id 是否连续
- 检查引用的 evidence id 是否真的存在
- 检查 plot 时间线是否单调

依赖：

- `models.py`

被谁调用：

- `pipeline.py`

在系统中的位置：

- deterministic validation 层

### [repair/repair_operator.py](/Users/yuezhao/Documents/New%20project/repair/repair_operator.py)

主要职责：

- 在 validation 失败时补局部步骤

输入：

- `CaseBible`
- `PlotPlan`
- `ValidationReport`

输出：

- 修复后的 `PlotPlan`

内部核心逻辑：

- 读取 issue code 集合
- 根据不同 code 附加新的 `PlotStep`
- 最后重新排序并重编号

当前局限：

- 它是启发式补丁，不会重写整个计划
- 如果原始 `PlotPlan` 和 `CaseBible` 差得太远，它只能缓解，不能根治

### [realization/story_realizer.py](/Users/yuezhao/Documents/New%20project/realization/story_realizer.py)

主要职责：

- 将结构化计划实现为自然语言故事

输入：

- `CaseBible`
- `PlotPlan`

输出：

- `str` 故事文本

内部核心逻辑：

- 如果 backend 是 `MockLLMBackend`
  - 使用简单拼接式 realization
  - 还会生成标题

- 如果 backend 是 `GeminiLLMBackend`
  - 会把 `CaseBible` 与 `PlotPlan` 转成大 prompt
  - 要求模型生成更自然的、分场景的叙事文本

当前局限：

- Mock 分支里仍然有旧模板痕迹，比如结尾固定提到“deleted footage”“digitalis trace”等旧案细节
- Gemini 分支是否能与 truth 对齐，很大程度取决于 `PlotPlan` 是否已经和 `CaseBible` 对齐

### [pipeline.py](/Users/yuezhao/Documents/New%20project/pipeline.py)

主要职责：

- 编排全链路

输入：

- `output_dir`
- `seed`

输出：

- 一个字典，包含运行过程中的关键结果对象

内部逻辑：

1. 创建输出目录
2. 同时实例化：
   - `self.mock_llm`
   - `self.gemini_llm`
3. 当前实际把 `self.gemini_llm` 传给：
   - `CaseBibleGenerator`
   - `StoryRealizer`
4. 顺序运行：
   - case generation
   - fact building
   - plot planning
   - validation
   - optional repair
   - realization
5. 保存所有输出文件

---

## 6. 一次完整运行时到底发生了什么

假设运行：

```bash
python main.py
```

程序会这样走：

1. [main.py](/Users/yuezhao/Documents/New%20project/main.py) 中的 `main()` 被执行。

2. `parse_args()` 读取：
   - `--output-dir`
   - `--seed`

3. `main()` 创建 `CrimeMysteryPipeline(output_dir=args.output_dir, seed=args.seed)`。

4. [pipeline.py](/Users/yuezhao/Documents/New%20project/pipeline.py) 的 `__init__()` 中：
   - 创建输出目录
   - 创建 `MockLLMBackend`
   - 创建 `GeminiLLMBackend`
   - 创建 `CaseBibleGenerator(llm=self.gemini_llm, ...)`
   - 创建 `FactGraphBuilder`
   - 创建 `PlotPlanner`
   - 创建 `PlotPlanValidator`
   - 创建 `PlotPlanRepairOperator`
   - 创建 `StoryRealizer(llm=self.gemini_llm)`

5. 调用 `pipeline.run()`。

6. `case_bible = self.case_generator.generate()`
   - 读取 `setting.txt`
   - 组织一个要求返回 JSON 的 prompt
   - 调用 Gemini
   - 提取 JSON
   - 解析并构造成 `CaseBible`

7. `fact_graph = self.fact_builder.build(case_bible)`
   - 按时间排序 timeline
   - 推断死亡时间、方法时间、角色窗口
   - 展开出 `FactTriple` 列表

8. `initial_plot_plan = self.plot_planner.build_plan(case_bible)`
   - 当前这里返回的是一套旧模板 plot steps
   - 这一点很重要，因为它可能和最新 `CaseBible` 不一致

9. `initial_report = self.validator.validate(case_bible, initial_plot_plan)`
   - validator 读取 case bible 和 plot plan
   - 产生 issues 与 metrics

10. 如果 `initial_report.is_valid` 为 `False`：
    - 调用 `repair_operator.repair(...)`
    - 再次 `validate(...)`

11. `story_text = self.story_realizer.realize(case_bible, final_plot_plan)`
    - 因为当前用的是 Gemini backend
    - 所以会走 `_realize_with_gemini()`
    - 把 `CaseBible + PlotPlan` 组织成 prompt
    - 让模型写出自然语言故事

12. pipeline 保存：
    - `case_bible.json`
    - `fact_graph.json`
    - `plot_plan.json`
    - `validation_report.json`
    - `story.txt`

13. `main.py` 最后打印：
    - setting 摘要
    - validation 是否通过
    - 输出目录

---

## 7. 输出文件说明

### `outputs/case_bible.json`

- 隐藏真相层
- 表示案件的 ground truth
- 是整个系统最上游的结构化结果

### `outputs/fact_graph.json`

- 从 `CaseBible` 编译出的事实层
- 用于把案件信息表达成统一的三元组格式

### `outputs/plot_plan.json`

- 调查计划层
- 是结构化 investigation beats，而不是最终小说文本

### `outputs/validation_report.json`

- 对 `plot_plan.json` 的校验结果
- 里面有：
  - 是否通过
  - 哪些规则失败
  - 基本计数指标

### `outputs/story.txt`

- 最终自然语言输出
- 当前它依赖 `CaseBible + PlotPlan`
- 因此只要 `PlotPlan` 仍然和 `CaseBible` 未完全对齐，`story.txt` 也可能继承这种不一致

### 这些输出之间的关系

- `case_bible.json`：隐藏真相层
- `fact_graph.json`：隐藏真相的机器事实层
- `plot_plan.json`：调查过程层
- `validation_report.json`：调查过程的规则检查层
- `story.txt`：最终自然语言叙事层

---

## 8. Validator 和 Repair 的机制详解

### 8.1 Validator 检查了什么

当前 validator 检查：

- 至少 4 个 suspects
- 至少 8 个 evidence items
- 至少 15 个 plot steps
- 至少 2 个 `alibi_check`
- 至少 1 个 `red_herring`
- 至少 1 个 `interference`
- culprit evidence chain 是否都被 plot plan 覆盖
- 是否存在 confrontation
- confrontation 是否包含关键证据
- culprit 是否被足够多步骤支持
- step_id 是否连续
- plot 中 evidence id 是否真的存在于 case bible
- plot 时间是否前后一致

### 8.2 为什么这些规则重要

- 这些规则对应课程项目的显式要求
- 它们保证系统不是“随便写一个推理故事”
- 而是至少在结构层面满足：
  - 嫌疑人够多
  - 线索够多
  - 有误导
  - 有 alibi check
  - 有 confrontation
  - 有可追踪证据链

### 8.3 Repair 是怎么修的

Repair 不是回到上游重新生成案件，而是：

- 缺 alibi，就补一个 alibi step
- 缺 interference，就补一个 interference step
- 缺 red herring，就补一个 red herring step
- culprit chain 没覆盖，就补一个 evidence step
- 没有 confrontation 或 confrontation 证据不足，就补 confrontation 或给已有 confrontation 加证据

### 8.4 当前 repair 的局限

- 它是启发式 patch，不是智能重规划
- 如果 `PlotPlanner` 与 `CaseBible` 差异太大，它很难彻底修正
- 它更适合修“小缺口”，不适合修“整体剧情模板错案”

---

## 9. LLM / Mock 机制详解

### 9.1 `llm_interface.py` 到底做了什么

它定义了统一接口：

```python
class LLMBackend:
    def generate(self, prompt: str) -> LLMResponse:
        ...
```

这样其他模块只关心：

- 输入一个 prompt
- 得到一个 `LLMResponse.text`

而不关心背后到底是 mock 还是真实 HTTP API。

### 9.2 Mock backend 的作用

`MockLLMBackend`：

- 不访问网络
- 适合做离线测试或结构演示
- 当前更像一个最小占位 backend

### 9.3 Gemini backend 的作用

`GeminiLLMBackend`：

- 当前使用 Gemini `generateContent` HTTP API
- 真实发送请求并获取文本输出

### 9.4 为什么默认不完全依赖 mock

当前实现已经把主流程切到了 Gemini：

- `CaseBibleGenerator` 用 Gemini
- `StoryRealizer` 用 Gemini

原因是你已经开始把“真相生成”和“故事实现”都接入真实大模型。

### 9.5 如果将来要替换模型，应该改哪里

主要改动点在：

- [llm_interface.py](/Users/yuezhao/Documents/New%20project/llm_interface.py)
- [pipeline.py](/Users/yuezhao/Documents/New%20project/pipeline.py)

如果要换成别的模型：

1. 新增一个实现 `LLMBackend` 的 backend 类
2. 在 `pipeline.py` 中切换传给 `CaseBibleGenerator` / `StoryRealizer` 的实例

---

## 10. 这个项目体现了哪些设计思想

### hidden truth vs revealed investigation

- `CaseBible` 是隐藏真相
- `PlotPlan` 是调查如何揭示真相
- 这两层是概念上分开的

### structure before prose

- 先有结构对象，再有故事文本
- `story.txt` 不是唯一输出，而是最后一步

### deterministic validation

- 校验由 `validator.py` 负责
- 不是让 LLM 说“我觉得这个计划合理”

### local repair instead of full regeneration

- 出问题时优先补丁，而不是整案重来
- 这让系统更像“规划 + 修复”流程

### separation of concerns

- case generation
- fact building
- planning
- validation
- repair
- realization

这些职责被拆在不同文件里，虽然实现还简化，但边界是清楚的。

---

## 11. 当前实现的简化之处与局限性

这一部分非常重要，需要诚实说明。

### 11.1 `PlotPlanner` 还没有跟上新的 `CaseBible`

这是当前最大局限。

- `CaseBibleGenerator` 已改为 Gemini 动态生成
- 但 `PlotPlanner` 仍是旧模板

结果就是：

- 上游真相层是动态的
- 中游调查计划层仍是静态旧案

这会导致：

- validator 报很多 mismatch
- story realizer 可能生成与 case bible 不一致的叙事

### 11.2 `StoryRealizer` 的 mock 分支仍有旧模板残留

比如它的 closing 中仍提到：

- deleted footage
- digitalis trace
- staged outage

这些不一定和当前动态案件一致。

### 11.3 `CaseBibleGenerator` 的校验还比较浅

它会检查：

- JSON 结构对不对
- 字段有没有
- 类型对不对
- culprit evidence chain 是否引用真实证据

但还不会深层检查：

- timeline 是否绝对严密
- 红鲱鱼是否足够强
- alibi 文本是否真的自洽

### 11.4 `FactGraphBuilder` 的时间推断仍然是启发式

虽然比之前强很多，但仍依赖：

- 时间排序
- 关键词
- summary 文本中是否出现特定动作词

它不是基于真正的事件语义解析。

### 11.5 Gemini 调用可能超时

当前真实使用了网络 API。

所以可能出现：

- timeout
- 网络不可达
- API 响应格式不稳定

这不是 mock 模式下会遇到的问题。

### 11.6 API key 当前实现仍然比较原型化

根据当前代码，`GeminiLLMBackend` 构造函数里仍保留了默认 key 字符串。

这对课程 demo 可能方便，但从工程角度不理想，后续更适合改为：

- 环境变量
- 本地配置文件
- 不在仓库中明文保存

---

## 12. 如何阅读这个项目

如果你第一次读这个仓库，建议按这个顺序：

### 第一步：先看 [pipeline.py](/Users/yuezhao/Documents/New%20project/pipeline.py)

原因：

- 它是全局入口
- 最容易理解模块之间怎么串起来

### 第二步：看 [models.py](/Users/yuezhao/Documents/New%20project/models.py)

原因：

- 先把数据结构弄清楚，再看各模块就容易很多

### 第三步：看 [generators/case_bible_generator.py](/Users/yuezhao/Documents/New%20project/generators/case_bible_generator.py)

原因：

- 它决定了上游 truth layer 怎么产生
- 也是最近变化最大的模块之一

### 第四步：看 [builders/fact_graph_builder.py](/Users/yuezhao/Documents/New%20project/builders/fact_graph_builder.py)

原因：

- 它展示了从叙事实体到结构事实的编译过程

### 第五步：看 [validators/validator.py](/Users/yuezhao/Documents/New%20project/validators/validator.py) 和 [repair/repair_operator.py](/Users/yuezhao/Documents/New%20project/repair/repair_operator.py)

原因：

- 这里体现了“验证 + 修复”的课程核心思想

### 第六步：看 [planners/plot_planner.py](/Users/yuezhao/Documents/New%20project/planners/plot_planner.py)

原因：

- 看完你会立刻明白当前系统最大的未对齐点在哪里

### 第七步：看 [realization/story_realizer.py](/Users/yuezhao/Documents/New%20project/realization/story_realizer.py)

原因：

- 这是最终把结构转成故事文本的地方
- 也能看出 Mock / Gemini 两种 realization 路径

---

## 13. 如何运行

### 13.1 依赖

当前项目只使用 Python 标准库，没有额外第三方依赖要求。

建议环境：

- Python 3.10+

### 13.2 启动命令

```bash
python main.py
```

也可以指定：

```bash
python main.py --output-dir outputs --seed 7
```

### 13.3 配置要求

因为当前主流程使用 `GeminiLLMBackend`，所以运行时需要：

- 网络可访问 Gemini API
- API key 可用

### 13.4 当前默认不是纯 mock mode

这一点要明确：

- 当前 pipeline 会同时实例化 Mock 和 Gemini
- 但真正传给核心模块的是 Gemini

也就是说，**当前默认运行模式是 Gemini 主流程，不是纯 mock**。

---

## 14. 从一个例子理解系统

以当前 `outputs/` 目录中常见的一次运行结果为例：

1. `case_bible.json`
   - 会给出一个完整的 manor mystery 案件
   - 比如 victim、culprit、suspects、timeline、evidence、red herrings、culprit evidence chain

2. `fact_graph.json`
   - 会把其中的信息编译成：
     - `is_victim`
     - `is_culprit`
     - `used_method`
     - `present_at`
     - `is_evidence`
     - `implicates`
     - `red_herring_explained_by`

3. `plot_plan.json`
   - 当前仍可能是旧模板调查计划
   - 所以你需要警惕它是否真的对应这个最新案件

4. `validation_report.json`
   - 如果 plot plan 与 case bible 对不上，这里通常会出现：
     - `unknown_evidence`
     - `evidence_chain`
     - `culprit_support`
     - `confrontation_evidence`

5. `story.txt`
   - 如果上游和中游已经对齐，它应该是结构到叙事的合理转换
   - 如果上游 truth 和 plot plan 仍未对齐，它会继承这种不一致

---

## 快速读码指南

如果你想用最短时间理解这个项目，建议只开这三个文件，按顺序看：

### 1. [pipeline.py](/Users/yuezhao/Documents/New%20project/pipeline.py)

先看这个文件，因为它告诉你：

- 系统有哪些阶段
- 每个阶段的顺序是什么
- 当前到底是 Mock 还是 Gemini 在驱动主流程

### 2. [models.py](/Users/yuezhao/Documents/New%20project/models.py)

再看这个文件，因为它决定了：

- 数据长什么样
- 模块之间到底传什么对象

把 schema 看明白后，其他模块都会好理解很多。

### 3. [generators/case_bible_generator.py](/Users/yuezhao/Documents/New%20project/generators/case_bible_generator.py)

第三个看它，因为当前系统最关键的变化都从这里开始：

- `setting.txt` 怎么被读取
- Gemini 怎么被 prompt 成结构化 JSON
- JSON 怎么被解析成 `CaseBible`

看完这三个文件后，再按这个顺序继续：

1. [builders/fact_graph_builder.py](/Users/yuezhao/Documents/New%20project/builders/fact_graph_builder.py)
2. [validators/validator.py](/Users/yuezhao/Documents/New%20project/validators/validator.py)
3. [repair/repair_operator.py](/Users/yuezhao/Documents/New%20project/repair/repair_operator.py)
4. [planners/plot_planner.py](/Users/yuezhao/Documents/New%20project/planners/plot_planner.py)
5. [realization/story_realizer.py](/Users/yuezhao/Documents/New%20project/realization/story_realizer.py)

这样你会先建立“真实数据流”的理解，再去看当前哪些地方已经成熟，哪些地方仍然需要继续改。
