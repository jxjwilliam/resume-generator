# profiles/ 目录说明 — YAML 文件对比

## ⭐ 新架构（2026-08）：内容源 + 定位配置

从 2026-08 起，目录分两类文件：

**内容源（Source）— 完整简历数据：**

| 文件 | 语言 | 用途 |
|---|---|---|
| `career-en.yaml` | EN | **英文内容唯一权威源**（默认 `--yaml`）。 |
| `base-zh-cto.yaml` | 中文 | 中国市场 CTO / 首席架构师完整简历。 |
| `base-zh-partner.yaml` | 中文 | 中国市场 AI 技术合伙人完整简历。 |

**定位配置（Positioning Profile）— 只描述"如何呈现"，内容来自 `source.career`：**

| 文件 | 市场 | 定位 |
|---|---|---|
| `na-ai-engineer.yaml` | Canada / NA | AI 侧重高级工程师 |
| `na-software-engineer.yaml` | Canada / NA | 传统 / 全栈高级工程师 |
| `china-cto.yaml` | China | CTO / AI 技术负责人 |
| `china-partner.yaml` | China | AI 技术合伙人 / 联合创始人 |

规则很简单：`python resume.py build --yaml profiles/na-ai-engineer.yaml`
会自动加载 `career-en.yaml`，再用 profile 里的 `headline` / `summary` /
`experience_priority` / `skills_priority` / `projects_priority` /
`recent_jobs` / `old_experience_max_bullets` 重新聚焦内容。实现见
`src/profiles.py`，完整说明见 `docs/profile-layering.md`。

旧版 `base.yaml` 仍可作为完整源文件加载，不再是默认值；
`base-v1/v2/v3.yaml`、`base-zh.yaml`、`base-2-zh.yaml` 已于 2026-08-17 删除。

---

> 下面章节是**已删除历史文件**的差异对比，仅存档参考，当前已不再使用。

本目录存放 6 个简历数据文件，内容高度相似（来自同一套经历/技能/项目数据），
但**版本、详略、语言和定位各不相同**。下表与矩阵帮助快速辨识和选用。

## 一、文件总览

| 文件 | 版本 | 语言 | 更新日期 | 定位 |
|---|---|---|---|---|
| **`base.yaml`** | 2.1 | EN | 2026-07-27 | ⭐ **当前默认源文件**（`resume.py --yaml` 默认值）。最新版，强调 Agentic / Multimodal AI |
| `base-v3.yaml` | 2.0 | EN | 2026-07-27* | 英文「精简版」：v2 的浓缩（header 版本号未同步改） |
| `base-v2.yaml` | 2.0 | EN | 2026-06-25 | 英文「详细版」：升级到 Principal AI 定位，项目带详细 bullet |
| `base-v1.yaml` | 1.0 | EN | 2026-06-10 | 最早版本：Node.js 全栈视角，数据最少，内容最旧 |
| `base-zh.yaml` | 2.0 | 中文 | 2026-06-25 | 中文「精简版」：对应 base-v3 家族的内容 |
| `base-2-zh.yaml` | 2.0 | 中文 | 2026-06-25 | 中文「详细版」：对应 base-v2 家族，面向中国市场（可驻场） |

\* `base-v3.yaml` 的 meta 仍写着 2.0 / 2026-06-25（从 v2 复制未改），文件实际修改时间是 2026-07-27。

**血缘关系**：

```
base-v1 ──> base-v2 ──> base-v3 ──> base.yaml（当前主线）
                      └──────> base-zh.yaml（中文精简）
base-v2 ─────────────> base-2-zh.yaml（中文详细）
```

## 二、一图速记（看这几个点即可辨识）

| 辨别点 | `base.yaml` | `base-v3.yaml` | `base-v2.yaml` | `base-v1.yaml` | `base-zh.yaml` | `base-2-zh.yaml` |
|---|---|---|---|---|---|---|
| headline 关键词 | **Multimodal AI** | Principal + RAG | Principal + RAG | Node.js | 首席 AI 工程师 | 首席AI + Agentic |
| 项目数量 | **12** | 9（无 bullet） | 9（带 bullet） | **3** | 9（无 bullet） | 9（带 bullet） |
| Best Buy 经历 | deprecated 1条 | deprecated 1条 | active 2条 | active 2条 | deprecated 1条 | active 2条 |
| EPAM 结束日期 | **2021-02**（已统一） | 2021-02 | 2021-02 | 2021-02 | 2021-02 | 2021-02 |
| 教育年份（西交大） | 1991–1995 | 1991–1995 | 1991–1995 | **1987–1991** | 1991–1995 | 1991–1995 |
| 技能 `ai_ml` 组 | 16 项（含 Multimodal/LLM-Wiki/Harness） | 13 项 | 13 项 | **无此分组** | 13 项 | 13 项 |
| Cloudflare / GCP·Azure 置灰 | Cloudflare 有，**GCP/Azure deprecated** | GCP/Azure active | GCP/Azure active | GCP/Azure active | GCP/Azure active | GCP/Azure active |
| Cover Letter 模板 | 5 | 5 | 5 | **3** | 5 | **7**（含工业AI/金融科技） |
| 中英双语字段 | — | — | — | — | — | 有 `company_en` / `name_en` |
| 独立 `languages` 段 | — | — | — | — | — | **有**（中英文水平） |

## 三、分节差异明细

### 1. identity（头衔 / 基本信息）

- **headline**：
  - `base.yaml` → `Senior Full-Stack & AI Engineer | Agentic AI • RAG • Multimodal AI | Python • TypeScript`
  - `base-v2/v3` → `Principal AI Engineer | LLM Orchestration • RAG • Agentic AI | Python • TypeScript`
  - `base-v1` → `Senior Full-Stack & AI Engineer | Node.js • Python | Agentic AI & AI Solutions`
  - `base-zh` → `首席 AI 工程师 | LLM 编排 • RAG • 智能体 AI | Python • TypeScript`
  - `base-2-zh` → `首席AI工程师 | LLM编排 · RAG架构 · Agentic AI | Python · TypeScript`
- **urls**：`base-v1` 只有 GitHub + LinkedIn（2 个）；其余文件均为 4 个（新增 GitHub-AI 项目 + Portfolio）。
- **location**：`base-2-zh` 与众不同 —— `加拿大·温哥华（可驻场广州/深圳/上海）`，明确面向中国市场；`base-zh` 为「温哥华，加拿大」。

### 2. summary（简介）

- `base-v1`：全栈 + 云平台 + REST API/CI/CD 视角。
- `base-v2`：Principal AI + 生产级 LLM/RAG/agentic 视角。
- `base-v3`：v2 的浓缩版（更短）。
- `base.yaml`：回到「Senior full-stack」表述，新增 **multimedia AI（vision/audio/multimodal）**、hundreds of millions of events/year、玩家教练领导力。
- `base-2-zh` 在 v2 英文基础上加了「数据优先、禁止虚构」等中文内容规则注释（头部注释不同）。

### 3. experience（工作经历）

| 公司 | 各文件差异 |
|---|---|
| **ZTE / FedEx** | `base-v1` FedEx 有 **4 条 bullet**（含 Global Clearance System、数据源集成的额外两条）；其余文件精简为 2 条。 |
| **Best Buy** | `base-v1`/`base-v2`/`base-2-zh`：`active`，2 条 bullet（360° 商品/保修/购物车）;<br>`base-v3`/`base.yaml`/`base-zh`：`deprecated`，1 条 bullet + note「高级 AI 岗自动过滤」 |
| **WebMD** | `base-v1` **4 条**（含广告桥接/文档存储/大数据管线等更多细节）；`base-v2`/`base-2-zh` 3 条（无 metrics）；`base-v3`/`base.yaml`/`base-zh` 3 条 **并带 `metrics`/`keywords`/`variants`**（量化表达） |
| **中软国际(HSBC)** | `base-v1` 公司名/头衔不同（「China Soft (HSBC)」/「Full-stack Engineer / Software Architect」）；其余均为「China Soft International (HSBC)」/「Software Architect / Full-Stack Engineer」 |
| **EPAM (Credit Suisse)** | 所有文件均 2 条 bullet，结束日期均已统一为 **2021-02**；其余差异在：`base-v1` 公司名「EPAM (Credit Suisse)」+ 头衔「React/Full-stack Engineer」；其余为「EPAM Systems (Credit Suisse)」/「Software Architect / Full-Stack Engineer」 |
| **Xperi** | `base-v1` 头衔「Senior Full-stack Engineer」6 条 bullet；其余「Senior Full-Stack & AI/ML Engineer」5 条 bullet |
| **Best IT Consulting** | `base-v1` 7 条 bullet（Node.js 主导 + 通用咨询描述，无具体客户名）；`base-v2`/`base-2-zh` 6 条（陕西煤业 RAG、CrewAI、LLM 选型、GCP/Azure 微服务）；`base.yaml` 走 agentic 化表述（Agentic-Invoice / memory-aware workflows），**不再单独夸 GCP/Azure** |

### 4. skills（技能）

- **分组差异**：`base-v1` 只有 `languages/frameworks/tools/ai_tools` 4 组，**没有 `ai_ml` 组**；其余文件均含 `ai_ml`（+`ai_dev_tools`）。
- **条目数量**：
  - `base-v1`：6 语言（无 Bash）、8 框架、15 工具、9 AI 工具。
  - `base-v2/v3/zh/base-2-zh`：7 语言、11 框架、13 ai_ml、15 工具、10 ai_dev_tools。
  - `base.yaml`（最多）：**13 框架**（+In-Memory/缓存/队列流、ETL/ELT），**16 ai_ml**（+Multimodal AI、LLM-Wiki/记忆系统、Harness/Loop/上下文工程），工具中**新增 Cloudflare**、**GCP 与 Azure 标记 deprecated**（只对特定 JD 启用的 note）。
- **云计算**：`base-v1` 为 `AWS/GCP/Azure` 对等 active；v2 之后改为 `AWS (EKS…)/GCP (Vertex AI…)/Azure (AKS…)`，并抬高到 advanced。
- **语言技能等级命名**：`base-2-zh` 用中文等级（专家/精通/熟练）；其余文件用英文（expert/advanced/intermediate）。

### 5. projects（项目）

| 文件 | 数量 | 详细度 |
|---|---|---|
| `base-v1` | **3** | 带 bullet（热门 AutoBidder / Site-RAG-Chatbot / MLDP） |
| `base-v2` / `base-2-zh` | 9 | **带 bullet**（每项目 2–3 条） |
| `base-v3` / `base-zh` | 9 | 仅名称 + 描述（无 bullet） |
| `base.yaml` | **12** | 仅名称 + 描述；**新增** Agentic Proposal Engine、Dual-LLM Memory Pipeline (LLM-Wiki+RAG)、AgenticOmni |

### 6. cover_letters（求职信模板）

- `base-v1`：3 个（backend / ai-fullstack / leadership）。
- `base-v2/v3/base-zh`：5 个（ai-principal / ml-engineering / backend / ai-fullstack / leadership）。
- `base.yaml`：5 个，但 ai-fullstack 文案增至含 Gemini / Azure OpenAI 与跨职能/固定合同表述。
- `base-2-zh`：**7 个**，独有 `industrial-ai-focused`（工业 AI/制造数字化转型）与 `fintech-focused`（金融科技/银行/资本市场）。

### 7. 独有字段（只有 `base-2-zh.yaml` 有）

- `meta.name` = "姜威廉"、新增 `name_en`、`lang: "zh-CN"`
- experience 条目含 `company_en`；projects 含 `name_en`；education 含 `institution_en`
- 独立的 `languages` 段（中文母语 / 英语流利）
- skills 分类中把 Agile/TDD 单独拆成 `methodologies` 组（其他文件放在 tools）

## 四、该用哪一个？

| 你的场景 | 用哪个 |
|---|---|
| 英文简历 / `resume.py` 默认构建 | **`base.yaml`**（唯一会被 `--yaml` 默认加载的文件） |
| 中文简历、内容从简 | **`base-zh.yaml`** |
| 中文简历、面向中国企业（含驻场、金融/工业专题、详细项目描述） | **`base-2-zh.yaml`** |
| 追溯旧表述 / 对比历史版本 | `base-v1.yaml` / `base-v2.yaml` / `base-v3.yaml`（均为历史存档，不建议用于新构建） |

> 注：`resume.py --locale zh-CN` 只切换字体与 WebUI 的默认 YAML 文件名；实际的 YAML 内容依赖 `--yaml` 指定，默认永远是 `profiles/base.yaml`。WebUI 的 Editor 页可通过目录下拉自由选择任意 `profiles/*.yaml` 编辑/预览。
