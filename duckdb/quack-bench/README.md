# DuckDB Quack Benchmark

DuckDB Quack 远程协议性能基准测试。在本地 loopback 环境下测量 Quack 协议开销、批量传输速度、写入性能。

## 快速开始

```bash
pip install duckdb>=1.5.3
```

**终端 1 — 启动 Quack Server：**
```bash
python quack_bench_server.py
```

**终端 2 — 运行基准测试：**
```bash
python quack_bench_client.py
```

## 测试项目

| 测试 | 说明 |
|------|------|
| Ping Latency | 单次查询往返延迟（local vs Quack overhead） |
| Count(*) | 服务器端聚合，不同数据量级 |
| Full Data Fetch | 10K / 100K / 1M 行全量流式读取 |
| Batch Write | CREATE TABLE AS SELECT 批量写入 |
| Serial Inserts | 逐行 INSERT 事务吞吐 |
| Aggregation Pushdown | AVG/MIN/MAX/STDDEV 在服务端执行 |
| Write Visibility | 写入立即可见性验证 |

## 预期结果（本地 loopback, DuckDB 1.5.3+）

| 测试项 | 预期值 |
|--------|--------|
| Quack overhead/query | ~1 ms |
| 10K 行全量读取 | ~3 ms (3M rows/s) |
| 100K 行全量读取 | ~25 ms (4M rows/s) |
| 批量写入 100K 行 | ~50 ms (2M rows/s) |
| 串行 INSERT | ~400 tx/s |

## 参考

- [DuckDB Quack 官方文档](https://duckdb.org/docs/current/quack/overview.html)
- [Quack 协议公告 + 官方基准](https://duckdb.org/2026/05/12/quack-remote-protocol)
- [GizmoSQL vs Quack 对比分析](../../gizmosql-vs-quack.md)
