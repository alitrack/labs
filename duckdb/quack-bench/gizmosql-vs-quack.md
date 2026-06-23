# GizmoSQL vs Quack — 全面深度对比

> 调研日期：2026-06-23 | 对比维度：协议架构 · 性能 · 生态 · 安全 · 部署 · 社区

---

## 一句话结论

**Quack 是 DuckDB 的"原生血管"，GizmoSQL 是 DuckDB 的"全副武装"。**
- 如果只需要让 DuckDB 实例互相通信 → **Quack**（零依赖、3.5x 更快、官方维护）
- 如果需要多协议客户端接入（JDBC/ODBC/BI 工具）→ **GizmoSQL**（全生态、企业安全）
- 两者不互斥：Nginx/Caddy 前端 + 各自后端可共存

---

## 一、性能实测对比

### 1.1 官方基准（DuckDB 团队，AWS m8g.2xlarge，跨机器 0.28ms ping）

| 测试项 | Quack | Arrow Flight (GizmoSQL) | PostgreSQL |
|--------|-------|------------------------|------------|
| 100K 行传输 | **0.07s** | 0.07s | 0.20s |
| 1M 行传输 | **0.24s** | 0.38s | 2.20s |
| 10M 行传输 | **0.89s** | 2.90s | 25.64s |
| 60M 行传输 | **4.94s** | 17.40s | 158.37s |
| 小事务吞吐 (8线程) | **5,434 tx/s** | 1,358 tx/s | 4,320 tx/s |

> 来源：DuckDB 官方博客 [Quack: The DuckDB Client-Server Protocol](https://duckdb.org/2026/05/12/quack-remote-protocol)  
> Arrow Flight 使用 GizmoSQL 作为服务端，两者内部引擎均为 DuckDB。

**关键发现：**
- Quack 在大批量传输中比 Arrow Flight (GizmoSQL) 快 **3.5x**（60M 行：4.94s vs 17.4s）
- Arrow Flight 在小数据量（100K）与 Quack 持平，但随数据量增大劣势扩大
- Quack 小事务吞吐是 Arrow Flight 的 **4x**（5,434 vs 1,358 tx/s）
- Arrow Flight 甚至不如 PostgreSQL 协议在小事务上（1,358 vs 4,320 tx/s）

### 1.2 本地实测（本机 loopback，DuckDB 1.5.3 + Python Quack 客户端）

本次在 WSL 环境下实际搭建 Quack Server（Python DuckDB 1.5.3）+ Client 完成以下测试：

```bash
# Server (1.5.3, localhost:9494):
LOAD quack;
CREATE TABLE t_large AS SELECT range AS id, random() AS val, 
  hash(range::VARCHAR) AS p FROM range(1000000);
CALL quack_serve('quack:localhost', token:='test_token_2026');

# Client:
CREATE SECRET (TYPE quack, TOKEN 'test_token_2026', SCOPE 'quack:localhost');
ATTACH 'quack:localhost' AS remote;
```

**实测数据：**

| 测试项 | 结果 |
|--------|------|
| Ping 延迟（Quack overhead） | **1.09ms**（本地基线 0.19ms） |
| count(*) 1M 行 | **9ms**（服务器端聚合，仅传单个值） |
| 全量取 10K 行 | 3.0ms（3.3M rows/s） |
| 全量取 100K 行 | 24.4ms（4.1M rows/s） |
| 批量写入 100K 行 | 49.8ms（2.0M rows/s） |
| 串行单条 INSERT | **402 tx/s**（本地 loopback，无网络延迟） |
| 写入立即可见 | ✅ 同连接 + 重连均立即读到 |
| DETACH → quack_query 无状态查询 | ✅ 正常 |

**解读：**
- 本地 loopback 串行 INSERT 仅 402 tx/s，说明 Quack 的当前瓶颈不在网络而在协议开销
- 批量写入 2M rows/s 非常优秀，DuckDB 内部向量化能力通过 Quack 完全保留
- 写入立即可见验证了 ACID 语义
- 1.09ms 单次 query overhead 极低，适合 AI Agent 的交互式查询

### 1.3 GizmoSQL 独立基准

GizmoSQL 的 TPC-H SF 1000（1TB）在 Azure 单机上 **161 秒完成，成本 $0.17**。这个数字与 Quack 不可直接对比——它衡量的是引擎+协议的综合表现，且机器规格不同。但体现了 GizmoSQL 的整体工程品质。

---

## 二、协议架构对比

| 维度 | Quack | GizmoSQL (Arrow Flight SQL) |
|------|-------|---------------------------|
| **协议** | HTTP/2，自定义 `application/duckdb` 序列化 | gRPC + Arrow Flight SQL（protobuf） |
| **序列化** | DuckDB 内部 WAL 序列化路径，**零转换** | Arrow IPC 列式格式，DuckDB→Arrow 需要转换 |
| **往返次数** | 单查询 1 次请求-响应 | 至少 2 次（GetFlightInfo + DoGet） |
| **依赖** | **零第三方依赖** | Apache Arrow 23.0.1、gRPC、jwt-cpp |
| **端口** | 9494 | 默认 31337（可配置） |
| **行级传输** | DataChunk 粒度流式 FETCH | Arrow RecordBatch 流式 |
| **过滤下推** | ✅ SQL 原生支持 | ✅ Flight SQL 协议支持 |
| **适用场景** | DuckDB↔DuckDB 高效通信 | 通用 SQL 客户端接入 |

**核心差异：**
Quack 的序列化路径是 DuckDB 内部格式的直接 HTTP 封装——数据从查询结果到网络包零转换。Arrow Flight 需要 DuckDB 内部格式 → Arrow C Data Interface → gRPC 序列化，多一层转换。这是性能差距的根本原因。

---

## 三、客户端生态

| 客户端类型 | Quack | GizmoSQL |
|-----------|-------|----------|
| DuckDB 原生 | ✅ ATTACH 'quack:...' | ❌ 需独立 ADBC 驱动 |
| Python | ✅ 同 DuckDB Python API | ✅ ADBC + SQLAlchemy + Ibis + Pandas + GeoPandas |
| JDBC | ⚠️ 第三方 [gizmodata/quack-jdbc](https://github.com/gizmodata/quack-jdbc) | ✅ 官方 JDBC（支持 DBeaver/DataGrip） |
| ODBC | ❌ 无 | ✅ 官方 ODBC |
| ADBC | ⚠️ PyPI `adbc-driver-quack` | ✅ Python/Go/C++ ADBC |
| CLI | ✅ DuckDB CLI 即客户端 | ✅ gizmosql CLI（psql 风格） |
| JS/TS | ❌ 无 | ✅ 官方 JS/TS |
| BI 工具 | ❌ 无直接支持 | ✅ Grafana/Metabase/Superset/Power BI/Tableau/QGIS |
| 数据工程 | ❌ 无 | ✅ dbt/SQLMesh/PySpark SQLFrame |
| iOS | ❌ | ✅ App Store ($0.99) |

**生态判断：**
- Quack 的生态由 DuckDB 社区自发扩展（quack-jdbc、adbc-driver-quack 均第三方）
- GizmoSQL 的生态由单一开发者（Philip Moore）系统性构建，覆盖全栈
- 如果只需要 DuckDB↔DuckDB，Quack 即开即用；如果需要 BI 工具/JDBC 客户端，GizmoSQL 是全栈方案

---

## 四、安全模型

| 安全特性 | Quack | GizmoSQL Core | GizmoSQL Enterprise |
|----------|-------|:---:|:---:|
| Token 认证 | ✅ 自动生成随机 token | — | — |
| 用户名+密码 | ❌ | ✅ SHA256 | ✅ |
| JWT | ❌ | ✅ HS256 自签名 | ✅ + RSA/JWKS OIDC |
| TLS | 需反向代理 | ✅ TLS 1.2+ | ✅ |
| mTLS | 需反向代理 | ✅ | ✅ |
| 自定义认证回调 | ✅ SQL Macro | ✅ 中间件链 | ✅ |
| SSO/OAuth | ❌ | ❌ | ✅ Keycloak/Azure AD/Google |
| 目录级权限 | ❌ | ❌ | ✅ JWT claims + glob |
| 查询授权 | ✅ SQL Macro（只读/读写） | ❌ | ✅ Statement Queue |
| KILL SESSION | ❌ | ❌ | ✅ |
| 审计日志 | ✅ `enable_logging('Quack')` | ✅ AccessLog 中间件 | ✅ + Catalog Logging |

**安全判断：**
- Quack 的安全模型是"最小化+可扩展"——默认 token，需要 TLS 和细粒度权限时挂反向代理
- GizmoSQL 的安全模型是"企业全栈"——从传输层到应用层到目录级权限，开箱即用
- 两者都支持自定义认证回调函数：Quack 用 SQL Macro，GizmoSQL 用 C++ 中间件

---

## 五、部署与运维

| 维度 | Quack | GizmoSQL |
|------|-------|----------|
| **安装** | `INSTALL quack; LOAD quack;` (v1.5.3+ 自动) | 单二进制下载 / Docker / Homebrew / MSI |
| **启动** | `CALL quack_serve('quack:localhost')` | `gizmosql_server -B duckdb --database-filename data.db` |
| **配置复杂度** | 极低（默认可用） | 中等（需配置密码、JWT、TLS 证书） |
| **容器化** | 社区 Dockerfile | 官方 5 种 Docker 变体 + Helm + K8s Operator |
| **健康检查** | ✅ HTTP GET `/` 返回 200 | ✅ 内置 Health Check |
| **优雅关闭** | `CALL quack_stop('quack:localhost')` | ✅ Signal handler + Graceful Shutdown |
| **运行时调节** | ✅ `SET GLOBAL` 动态配置 | ✅ `SET GLOBAL` + Enterprise 专属 |
| **日志** | ✅ `enable_logging('Quack')` 结构化日志 | ✅ AccessLog + Telemetry (OTel) |
| **监控** | 日志输出（可接外部系统） | ✅ OTel 追踪 + Enterprise Session Instrumentation |
| **二进制体积** | 0（DuckDB 内置扩展） | ~50MB 静态编译 |
| **跨平台** | 有 DuckDB 的地方就能跑 | ✅ Linux/macOS/Windows/iOS |

---

## 六、社区与长期风险

| 维度 | Quack | GizmoSQL |
|------|-------|----------|
| **维护者** | DuckDB Labs + DuckDB Foundation | **1 人**（Philip Moore） |
| **成熟度** | Beta（v2.0 稳定版预计 2026.9） | Production（v1.32.0，Apache 2.0） |
| **GitHub Stars** | duckdb-quack 独立仓库 | 331 |
| **社区活跃度** | DuckDB 社区（18K+ stars）驱动 | 单一维护者 |
| **Bus Factor** | 🟢 高（DuckDB Labs 团队） | 🔴 **1**（关键风险） |
| **商业支持** | DuckDB Labs 商业支持 | GizmoData LLC（Philip Moore 个人公司） |
| **许可证** | MIT | Core: Apache 2.0 / Enterprise: 商业许可 |
| **路线图** | 复制协议、DuckLake catalog、稳定版 | 持续迭代（2-3 天/版本） |

**风险评估：**
- Quack 的 bus factor 极低——DuckDB 核心团队维护，协议已集成到 DuckDB 主线代码
- GizmoSQL 的 bus factor = 1 是最大风险——Philip Moore 不可替代
- 但 GizmoSQL 的项目工程品质（44 测试 + 6 平台 CI + 完整文档）远超单人项目的平均水平
- 如果 DuckDB 团队未来在 Quack 上增加 JDBC/ODBC 原生支持，GizmoSQL 的生态优势将被大幅削弱

---

## 七、与你项目的关联分析

| 场景 | 推荐方案 | 理由 |
|------|----------|------|
| **ChatSQL MCP**（AI Agent NL2SQL） | **Quack** | 低延迟、协议最简、DuckDB 原生、无额外依赖 |
| **NPP**（Web UI + 多用户） | **GizmoSQL** | JDBC/Grafana/Superset 全生态、多租户安全 |
| **cc**（AI 编程助手） | **Quack** | 同进程通信，零部署成本 |
| **跨语言客户端接入**（Java/Python/JS） | **GizmoSQL** | 全语言 ADBC + JDBC + ODBC |
| **数据湖查询**（DuckLake + S3） | **Quack** | DuckDB 原生 DuckLake 集成更好 |
| **企业 BI 场景** | **GizmoSQL Enterprise** | Power BI/Tableau + SSO/OAuth + 审计 |
| **最小化部署** | **Quack** | 零依赖，3 行 SQL 启动 |
| **高并发写入** | **Quack** | 4x 小事务吞吐优势 |

**个人 IP 项目建议：**
- `ChatSQL` 应优先集成 Quack 作为 DuckDB 远程访问层——延迟最低、依赖最少、与 DuckDB 版本同步升级
- 保留 GizmoSQL 作为备选方案，当需要 JDBC/ODBC 接入时切换
- `OntoMind` 如果需要多数据库后端，可参考 GizmoSQL 的双后端架构（DuckDB + SQLite）设计

---

## 八、总结矩阵

| | Quack | GizmoSQL | 胜出 |
|---|-------|----------|:---:|
| **批量传输性能** | 4.94s (60M) | 17.4s (60M) | 🏆 Quack |
| **小事务吞吐** | 5,434 tx/s | 1,358 tx/s | 🏆 Quack |
| **单次查询延迟** | ~1ms overhead | ~2+ trips | 🏆 Quack |
| **客户端生态** | DuckDB only + 第三方 | 全栈 JDBC/ODBC/BI | 🏆 GizmoSQL |
| **安全能力** | 基础 Token + 反向代理 | 企业全栈 TLS/JWT/SSO | 🏆 GizmoSQL |
| **部署简易度** | 3 行 SQL | 二进制 + 配置 | 🏆 Quack |
| **运维能力** | 日志 + 外部系统 | Health + OTel + Audit | 🏆 GizmoSQL |
| **依赖复杂度** | 零 | Arrow + gRPC + jwt-cpp | 🏆 Quack |
| **Bus Factor** | 高（DuckDB 团队） | 1 | 🏆 Quack |
| **生产就绪** | Beta | Production | 🏆 GizmoSQL |
| **许可** | MIT | Apache 2.0 + 商业 | 平手 |
| **代码质量** | DuckDB 核心代码 | 44 测试 + 6 CI | 🏆 GizmoSQL |

---

## 参考来源

1. [DuckDB — Quack: The Client-Server Protocol](https://duckdb.org/2026/05/12/quack-remote-protocol)（官方基准测试）
2. [DuckDB Quack 文档](https://duckdb.org/docs/current/quack/overview.html)
3. [GizmoSQL GitHub](https://github.com/gizmodata/gizmosql)
4. [GizmoSQL 深度调研报告](/mnt/d/wsl2/claw/wiki/gizmosql-deep-research.md)（#2026062101）
5. [DuckDB Quack 实战指南](/mnt/d/wsl2/claw/wiki/raw/articles/duckdb-quack-practical-guide.md)（#2026061701）
6. 本地实测：WSL DuckDB 1.5.3 Python Quack Server + Client，loopback 模式
7. [MotherDuck — Arrow Flight SQL vs REST vs JDBC](https://motherduck.com/blog/flight-sql-vs-rest-vs-jdbc/)
