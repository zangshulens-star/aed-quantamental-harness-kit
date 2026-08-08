# Index + Chaptered Docs — 规范

> 大型 agentic 项目的文档系统规范：主索引 + 章节分拆，防止文档随项目变大而失效。
> 来源：从一个 21-agent、~330K LOC 生产系统的工程文档实践抽象。

---

## 1. 它防的三个 Failure Mode

### 1.1 Compression Amnesia（压缩失忆）

LLM 上下文被压缩/截断后，agent 忘记项目全貌，重复劳动或推翻已定决策。

**对策**：主索引永远 <200 行，只放"系统画像 + 章节看板 + 快速查找表"。压缩后 agent 读一个文件即可恢复全貌，不需要读几十份文档。

### 1.2 Doc Rot（文档腐化）

文档越写越多、越写越旧，最终没人信、没人维护，agent 读到过期信息做出错误实现。

**对策**：分两类文档，各有铁律——
- **设计规格（architecture/）**：只放当前有效设计，**设计变更时更新，永不追加历史**。过期即改写，不存在"曾经是"的内容。
- **进度日志（chapters/implementation.md）**：只可追加，保留历史。两类文档的腐败通道被分别堵死。

### 1.3 Agent 读错文件（上下文污染）

agent 凭直觉打开错误的文档（旧版、归档、别的章节的），在错误前提下工作。

**对策**：**强制阅读协议**（§3）——索引是唯一的入口，查找表直接定位到正确章节；禁止跳过索引直接读细节文档；归档目录（`v1_archive/`、`_archived/`）显式标记永不编辑、不被活跃代码 import。

---

## 2. 三层结构

```
docs/
  ENGINEERING_INDEX.md          ← 主索引（唯一入口，<200 行）
  architecture/                 ← 共享设计规格（变更时更新，永不追加）
    01_<domain>.md
    02_<domain>.md
    ...
  chapters/
    chNN_<domain>/
      plan.md                   ← 本章节设计 + 实施计划（≤200 行）
      implementation.md         ← 进度日志 + 交付清单（≤200 行，只追加）
  memo/                         ← 对话备忘（自由格式，不进 docs）
```

**各层职责**：

| 层 | 角色 | 更新规则 |
|----|------|---------|
| ENGINEERING_INDEX | 系统画像、Chapter 看板、Sprint 看板、§4 快速查找表 | 结构性变化时更新 |
| architecture/NN_*.md | 跨章节共享的设计契约（agent catalog / data schema / orchestration） | 设计变更即改，不留历史 |
| chapters/plan.md | 单章节任务分解 + 验收标准 | 实施前对齐，任务变更时更新 |
| chapters/implementation.md | 进度日志 + 交付清单 + 测试结果 | 实施后追加，保留历史 |

---

## 3. Agent 阅读协议（强制）

每次实施前，按顺序：

1. 先读 `docs/ENGINEERING_INDEX.md`——确认当前 Sprint、Chapter 状态、关键依赖
2. 用 §4 快速查找表定位相关 Chapter
3. 读对应 `chapter/plan.md`——确认任务分解和验收标准
4. 读对应 `chapter/implementation.md`——确认当前进度和已完成项
5. 涉及数据/协议变更时，读 `architecture/` 对应规格

**禁止**：
- 跳过 Index 直接读 plan/implementation
- 编辑归档目录下任何文件
- 在根级 `docs/` 直接新建文件（新内容必须归入子目录）

---

## 4. 写作规则

1. **每份文档头一行是定位行**：`> 这份文档是什么 + 它的更新规则`（例：`> 设计变更时更新，永不追加历史`）
2. **交叉引用显式**：每个章节末尾列"关联阅读"，不允许"见上文"式悬空引用
3. **代码引用必须全路径**：相对项目根目录的完整路径
4. **数字必须可核实**：行数、字段数、覆盖率等必须来自实际执行日志，不允许约数
5. **自包含章节**：每章可独立阅读；共同内容放 architecture/ 而不是章间互相引用

---

## 5. 与 Task Tracking Protocol 的关系

本规范管**文档结构**，TTP 管**任务状态**。两者的接合点：Bootstrapping 时 TTP 从 `ENGINEERING_INDEX.md`（首选）或 `CLAUDE.md`（fallback）提取 Project Snapshot 和 Handoff Blob。文档系统是 TTP 的上下文来源。

---

## 模板

见 `templates/`：
- `ENGINEERING_INDEX.template.md`
- `chapter_plan.template.md`
- `chapter_implementation.template.md`
