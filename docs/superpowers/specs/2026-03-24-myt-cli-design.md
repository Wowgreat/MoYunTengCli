# 魔云腾盒子 CLI 工具设计文档

日期：2026-03-24

## 1. 目标

构建一个面向魔云腾盒子的命令行工具，提供以下能力：

- 备份指定云机
- 从已有备份恢复出新云机
- 启动指定云机
- 查询云机列表与状态

第一版同时满足两种使用方式：

- 手动在命令行执行
- 被 Windows 任务计划定时调用，实现自动备份

第一版不包含页面、数据库、多用户权限和内置调度器。

## 2. 范围

### 2.1 包含范围

- 基于盒子 Swagger 接口进行调用
- 按云机名称作为主要输入方式
- 程序内部将名称解析为唯一云机 ID 后执行具体操作
- 支持日志记录
- 支持异步任务轮询
- 支持失败报错和超时处理

### 2.2 不包含范围

- Web 页面
- 批量任务管理平台
- 数据库存储
- 消息通知
- 从镜像或模板导入云机

## 3. 交互形式

工具以 CLI 形式交付。建议命令如下：

```bash
myt-cli list
myt-cli status --name 云机A
myt-cli backup --name 云机A
myt-cli restore --backup 备份A --target 云机A-恢复
myt-cli start --name 云机A
```

说明：

- `list`：列出当前可见云机的名称、ID、状态
- `status`：查询指定云机状态
- `backup`：对指定云机创建备份
- `restore`：从已有备份恢复出一台新云机
- `start`：启动指定云机

## 4. 配置设计

配置文件采用 YAML，负责保存环境配置与默认行为。建议结构如下：

```yaml
box:
  base_url: "http://10.0.103.227:8000"
  token: "your-token"
  timeout_seconds: 30

task:
  poll_interval_seconds: 5
  timeout_seconds: 1800

backup:
  name_template: "{vm}_{date}_{time}"

logging:
  level: "INFO"
  file: "logs/myt-cli.log"
```

设计原则：

- 盒子地址、认证、超时、轮询间隔放配置文件
- 操作目标通过命令参数传入
- 自动备份由 Windows 任务计划调用 CLI 命令完成，不在程序内实现常驻调度

## 5. 架构设计

建议采用轻量分层结构：

```text
myt_cli/
  app.py
  config.yaml
  client.py
  cli.py
  polling.py
  exceptions.py
  services/
    vm_service.py
    backup_service.py
    restore_service.py
    start_service.py
```

模块职责如下：

### 5.1 `client.py`

- 封装所有 HTTP 请求
- 统一处理 `base_url`、认证头、超时
- 解析统一响应结构
- 将接口失败转换为程序内部异常

### 5.2 `cli.py`

- 解析命令参数
- 分发到对应的 service
- 统一控制台输出格式

### 5.3 `polling.py`

- 轮询异步任务状态
- 统一处理轮询间隔、超时、成功和失败状态

### 5.4 `services/vm_service.py`

- 按名称查询云机
- 校验名称唯一性
- 获取云机详情和当前状态

### 5.5 `services/backup_service.py`

- 创建备份
- 生成默认备份名
- 轮询备份任务状态
- 返回备份结果

### 5.6 `services/restore_service.py`

- 按备份名称或 ID 查找备份
- 校验目标云机名称是否冲突
- 发起恢复任务
- 轮询恢复完成
- 返回新云机信息

### 5.7 `services/start_service.py`

- 查询云机当前状态
- 若已运行则直接返回
- 若未运行则发起启动
- 轮询至运行态

## 6. 执行流程

### 6.1 备份流程

输入：

- 云机名称

执行步骤：

1. 按名称查找云机
2. 确保只匹配到一台
3. 检查当前状态是否允许备份
4. 依据模板生成备份名
5. 调用创建备份接口
6. 若接口返回任务 ID，则轮询任务状态
7. 成功后输出备份名、任务 ID 和最终状态

### 6.2 恢复流程

输入：

- 备份名称或备份 ID
- 目标云机名称

执行步骤：

1. 查找备份并确认唯一
2. 检查目标云机名称未被占用
3. 调用恢复接口
4. 获取恢复任务 ID
5. 轮询恢复任务状态
6. 恢复成功后查询新云机信息
7. 输出新云机名称、ID 和状态

### 6.3 启动流程

输入：

- 云机名称

执行步骤：

1. 按名称查找云机
2. 查询当前状态
3. 若已处于运行态，直接返回成功
4. 否则调用启动接口
5. 若接口返回任务 ID，则轮询任务状态
6. 最终确认云机进入运行态

### 6.4 状态查询流程

输入：

- 云机名称

执行步骤：

1. 按名称查找云机
2. 查询云机详情和状态
3. 输出名称、ID、状态

## 7. 异常与边界处理

建议定义以下异常类型：

- `VMNotFoundError`
- `VMMultipleFoundError`
- `BackupNotFoundError`
- `BackupMultipleFoundError`
- `TargetNameConflictError`
- `ApiRequestError`
- `TaskTimeoutError`
- `TaskFailedError`
- `ConfigError`
- `AuthError`

关键规则：

- 名称查到多个结果时必须失败，不做模糊猜测
- 已启动的云机再次启动时应返回成功，而不是报错
- 目标恢复名称已存在时必须提前阻止
- 所有异步任务都必须记录任务 ID

## 8. 日志设计

程序需要同时输出控制台日志和文件日志。

日志记录的核心字段包括：

- 时间
- 命令类型
- 云机名称
- 云机 ID
- 备份名称或备份 ID
- 任务 ID
- 执行结果
- 错误原因
- 耗时

示例：

```text
2026-03-24 18:00:00 INFO action=backup vm_name=云机A vm_id=123 backup_name=云机A_20260324_180000 task_id=t001 status=success duration=125s
2026-03-24 18:05:00 ERROR action=restore backup=备份A target=云机A-恢复 status=failed reason=target_name_exists
```

控制台输出保持简洁，便于人工查看：

```text
[OK] backup completed: vm=云机A backup=云机A_20260324_180000 task=t001
[FAIL] restore failed: target name already exists
```

## 9. 自动备份方案

自动备份不通过程序内置调度器实现，而通过 Windows 任务计划定时调用 CLI。

示例：

```bash
python app.py backup --name 云机A
```

这样设计的原因：

- 实现简单
- 不需要常驻进程
- 稳定性更高
- 排查链路更清晰

## 10. 依赖接口

在正式实现前，需要从盒子 Swagger 中确认以下接口：

- 云机列表或查询接口
- 云机详情接口
- 备份创建接口
- 备份列表或备份查询接口
- 从备份恢复云机接口
- 启动云机接口
- 任务状态查询接口
- 认证方式及鉴权头要求

## 11. 开发顺序

建议按以下顺序开发：

1. 实现基础 HTTP 客户端与认证
2. 实现云机查询与按名称唯一匹配
3. 实现启动流程，验证基础闭环
4. 实现备份流程
5. 实现恢复流程
6. 接入统一日志
7. 配置 Windows 任务计划完成自动备份
8. 补充使用文档与常见错误说明

## 12. 成功标准

第一版完成后，应满足以下标准：

- 可通过 CLI 按名称备份指定云机
- 可从已有备份恢复出一台新云机
- 可按名称启动指定云机
- 可查询云机列表与状态
- 所有关键操作有日志可追踪
- 支持由 Windows 任务计划稳定调用实现自动备份
