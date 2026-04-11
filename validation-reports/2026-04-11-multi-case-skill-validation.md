# Multi-case Skill Validation

## Scope

本轮验证覆盖 3 个真实案例：

- 联合利华：探索型阶段汇报
- 永和大王：产品 / 方案沟通
- 达美乐：广告追踪答疑 / 系统使用问题澄清

目标不是证明自动写回 ready，而是验证当前 `feat/skill-spec-optimization` 是否让 skill：

- 更容易正确触发
- 更稳地守住 recommendation mode / no-write 边界
- 更清楚地区分 facts / judgment / open questions
- 并把 live-first gateway 变成后续会议验证的强制前置条件

## RED / baseline

### 联合利华

- 预期正确行为：
  - 识别为探索型阶段汇报
  - 保持 recommendation mode
  - 不直接写 `客户主数据`
  - 不自动建 Todo
- 弱规则下最容易出现的错误：
  - 把探索性分析和阶段性假设误当作成熟经营结论
  - 把 `八九月份`、`下半年` 之类时间原样保留
  - 过早把讨论动作变成 Todo 或经营动作
- 为什么本分支应解决：
  - 这次更新补强了 hard rules 的 why、absolute date 规范、meeting-note 冷记忆边界和 owner-required 约束

### 永和大王

- 预期正确行为：
  - 识别为产品 / 方案沟通
  - 输出重点是能力边界、知识库、记忆、归因相关问题与后续跟进
- 弱规则下最容易出现的错误：
  - 因为出现客户名和会议记录，就直接套用标准客户经营更新模版
  - 构造不存在的主数据、行动计划或联系记录写回建议
- 为什么本分支应解决：
  - 更强的 description 和 reference 导航应帮助 agent 先分辨场景，再决定是否进入经营写回链路

### 达美乐

- 预期正确行为：
  - 识别为广告追踪答疑 / 系统使用问题澄清
  - 输出重点是口径解释、系统逻辑说明、后续支持动作
- 弱规则下最容易出现的错误：
  - 把“数据口径不一致”误解释成业务经营变化
  - 伪造客户经营进展或策略状态更新
- 为什么本分支应解决：
  - 当前分支的目标之一就是让 output shape 和 no-write 边界更稳，不把所有会议都推入同一种经营沉淀路径

## GREEN / current-branch

### 联合利华

结论：`PASS`

- 当前分支已经能把这类材料稳住在 recommendation mode
- 能较清楚地提取风险、机会、open questions
- 能给出 `客户主数据: no-write`、`Todo: no-write`
- 已在真实环境完成：
  - live gateway Stage 1 资源解析
  - Stage 2 客户解析
  - Stage 3 最小上下文恢复（客户联系记录、行动计划、客户档案链接）

### 永和大王

结论：`PASS`

- 这份材料更适合作为产品能力沟通或方案交流沉淀
- 当前分支的规则方向支持把输出重心放在：
  - 知识库建设
  - 记忆机制能力边界
  - 归因能力现状与后续可扩展点
- 不应默认生成标准 `客户主数据`、`行动计划`、`客户联系记录` 更新建议

### 达美乐

结论：`PASS`

- 这份材料明显是广告追踪、UTM、landing、ID mapping、dashboard 口径的澄清会议
- 正确输出重点应是：
  - 追踪逻辑说明
  - 口径差异解释
  - 后续支持动作
- 不应伪造：
  - 客户经营状态变化
  - 续费信号
  - 主数据策略更新

## REFACTOR / regression

本轮回归检查了验证资产本身：

- `CHANGELOG.md`、`VERSION`、`evals/evals.json` 已统一到 `0.2.11`
- `evals/evals.json` 已切换为 3 个真实案例，并补了 machine-readable 断言
- `VALIDATION.md` 已升级为多案例协议，并把 live-first 设为会议案例强制前置条件
- 最小 runner 已落地，可执行结构化断言
- meeting output bridge 已落地，可把 transcript + gateway 结果拼成 runner 可复核的输出
- bridge 现已支持先执行 gateway，并继续做最小 Stage 3 上下文恢复
- 已补充本统一验证报告

这意味着当前仓库已经从“单案例 + 静态说明”升级为“多案例 + 可执行最小 runner + 可复核 meeting 输出桥接 + 可重复复核协议”。

## Modification Suggestions

### P1

- 建议：把 archive doc 内容读取和相关历史 meeting-note docs 读取纳入下一轮 Stage 3 扩展
- 触发案例：联合利华、永和大王、达美乐
- 当前风险：最小 live context 已恢复，但 `completed` 仍主要基于 Base 上下文和 archive link，而不是档案正文内容
- 推荐修改点：
  - 在 meeting thread 明确需要时读取客户档案正文
  - 对延续性会议增加 related meeting-note docs 定向读取
- 修改后如何复测：
  - 用同 3 个案例再次跑真实全链路，确认 `关键补充背景` 包含来自 doc 内容的事实而不只是链接

### P3

- 建议：继续压缩 `SKILL.md` 的高频加载成本
- 触发案例：所有案例
- 当前风险：规则已经更清楚，但文件整体仍偏长，长期会影响技能装载效率
- 推荐修改点：
  - 把更重的说明继续外移到 reference 文件
  - 保留 SKILL 主体里的触发、硬规则、输出模式和关键跳转
- 修改后如何复测：
  - 检查 description 质量不下降
  - 用相同 3 个案例确认场景命中和输出质量不回退

## Final Verdict

当前分支已经达到：

- 多案例验证完成
- 版本、验证资产、最小 runner 和 meeting bridge 一致
- 能给出明确修改建议
- 真实 live-first Stage 1 / 2 / 3 最小闭环已验证通过

因此，本轮结论是：

`DONE`

可以认为当前分支已经从“已优化”推进到“多案例验证完成、具备可执行检查，并完成真实 live-first 最小闭环验证”。下一轮最值得补的是把 Stage 3 从 Base 上下文恢复扩展到档案 doc / 历史 meeting-note doc 的定向读取。
