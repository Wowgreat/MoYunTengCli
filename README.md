# MoYunTengCli

`MoYunTengCli` 是一个面向魔云腾盒子的 Python 工具包，既可以作为命令行工具使用，也可以作为第三方库被其他项目直接引用。

兼容的 Python 版本范围：

- `Python 3.7`
- `Python 3.8`
- `Python 3.9`
- `Python 3.10`
- `Python 3.11`
- `Python 3.12`

当前已实现的核心能力：

- 按名称查询云机列表和状态
- 启动、关机、删除云机
- 导出云机备份
- 从备份恢复新云机
- 查询、设置、停止云机 S5 代理

项目基于以下官方文档实现第一版接口封装：

- 盒子管理接口：`heziSDKAPI`
- 云机内部 Android 接口：`MYT_ANDROID_API`

由于不同盒子固件版本、网络模式、Swagger 实际返回结构可能存在差异，当前项目采用“集中封装、便于微调”的实现方式。  
如果你的真实环境和公开文档存在字段差异，优先修改 [myt_cli/client.py](C:/code/myt/myt_cli/client.py) 和 [myt_cli/services/](C:/code/myt/myt_cli/services) 下的解析逻辑。

项目地址：

- GitHub: https://github.com/Wowgreat/MoYunTengCli

## 功能概览

CLI 命令：

- `list`
- `status`
- `start`
- `stop`
- `delete`
- `backup`
- `restore`
- `s5-status`
- `s5-set`
- `s5-stop`

Python API：

- `MytApp`
- `create_app`
- `create_app_from_path`

## 安装

### 本地开发安装

```bash
pip install -e .
```

安装后可以直接使用：

```bash
myt-cli --help
```

也可以继续沿用兼容入口：

```bash
python app.py --help
python -m myt_cli --help
```

### 依赖

项目依赖：

- `requests`
- `PyYAML`

如果不使用 `pip install -e .`，也可以手动安装：

```bash
pip install requests PyYAML
```

## 配置

默认配置文件名为 `config.yaml`。

示例：

```yaml
box:
  base_url: "http://10.0.103.227:8000"
  timeout_seconds: 30
  verify_ssl: false
  auth:
    type: "basic"
    username: "admin"
    password: "change-me"

task:
  poll_interval_seconds: 5
  timeout_seconds: 1800

backup:
  name_template: "{vm}_{date}.zip"
  download_dir: "artifacts/backups"

restore:
  max_index_num: 24

logging:
  level: "INFO"
  file: "logs/myt-cli.log"
```

配置说明：

- `box.base_url`
  - 盒子管理接口地址
  - 通常是 `http://盒子IP:8000`

- `box.auth.type`
  - 当前支持：
    - `none`
    - `basic`
    - `bearer`

- `restore.max_index_num`
  - 用于恢复云机时自动寻找空闲坑位
  - 如果设备是 `Q1`，通常应改为 `12`
  - 如果设备是 `P1`，通常为 `24`

- `logging.file`
  - 命令执行日志输出位置

## 命令行用法

### 1. 查看云机列表

```bash
myt-cli --config config.yaml list
```

### 2. 查看指定云机状态

```bash
myt-cli --config config.yaml status --name 001
```

### 3. 启动云机

```bash
myt-cli --config config.yaml start --name 001
```

### 4. 关闭云机

```bash
myt-cli --config config.yaml stop --name 001
```

### 5. 删除云机

```bash
myt-cli --config config.yaml delete --name 001
```

说明：

- 删除前建议先停机
- 删除是不可恢复操作

### 6. 备份云机

```bash
myt-cli --config config.yaml backup --name 001
```

说明：

- 当前严格按文档实现
- 使用的是盒子接口 `POST /android/export`
- 该接口只支持传入云机名称
- 备份文件名由盒子生成，程序读取返回的 `exportName`

### 7. 从备份恢复云机

自动选择空闲坑位：

```bash
myt-cli --config config.yaml restore --backup 001_20260324.zip --target 001-restore
```

手动指定坑位：

```bash
myt-cli --config config.yaml restore --backup 001_20260324.zip --index-num 2 --target 001-restore
```

说明：

- 当前实现流程：
  1. 从盒子备份列表中查找备份
  2. 通过 `/backup/download` 下载备份文件
  3. 再调用 `/android/import` 导入
- 如果不传 `--index-num`，程序会自动查找第一个空闲实例位
- 如果没有空闲坑位，程序会直接报错并退出

### 8. 查询 S5 代理状态

```bash
myt-cli --config config.yaml s5-status --name 001
```

示例输出：

```text
VM: 001
Android API: 10.0.103.227:30001
S5状态: 已启动
代理地址: socks5://user:password@host:port
代理模式: 2
消息: query success
```

### 9. 设置 S5 代理

推荐参数写法：

```bash
myt-cli --config config.yaml s5-set --name 001 --ip tunpool.example.com --port 27297 --user test --password secret --type 2
```

兼容旧参数名：

```bash
myt-cli --config config.yaml s5-set --name 001 --proxy-ip tunpool.example.com --proxy-port 27297 --proxy-user test --proxy-password secret --proxy-type 2
```

参数说明：

- `--ip`
  - 代理服务器地址
- `--port`
  - 代理服务器端口
- `--user`
  - SOCKS5 用户名
- `--password`
  - SOCKS5 密码
- `--type`
  - `1`：本地域名解析
  - `2`：服务端域名解析

### 10. 停止 S5 代理

```bash
myt-cli --config config.yaml s5-stop --name 001
```

## Python API 用法

### 从配置文件创建应用对象

```python
from myt_cli import create_app_from_path

app = create_app_from_path("config.yaml")
```

### 查询云机

```python
from myt_cli import create_app_from_path

app = create_app_from_path("config.yaml")

vms = app.list_vms()
vm = app.get_vm_status("001")

print(vms)
print(vm)
```

### 启动、关机、删除

```python
from myt_cli import create_app_from_path

app = create_app_from_path("config.yaml")

app.start_vm("001")
app.stop_vm("001")
app.delete_vm("001")
```

### 备份和恢复

```python
from myt_cli import create_app_from_path

app = create_app_from_path("config.yaml")

backup_result = app.backup_vm("001")

restore_result = app.restore_backup(
    backup_name="001_20260324.zip",
    target_name="001-restore",
)

print(backup_result)
print(restore_result)
```

### S5 代理

```python
from myt_cli import create_app_from_path

app = create_app_from_path("config.yaml")

status = app.get_s5_status("001")

app.set_s5_proxy(
    name="001",
    proxy_ip="tunpool.example.com",
    proxy_port=27297,
    proxy_user="test",
    proxy_password="secret",
    proxy_type=2,
)

app.stop_s5_proxy("001")

print(status)
```

## 设计说明

### 1. CLI 和 Python API 共用同一套底层实现

命令行和库调用不是两套逻辑。  
它们都基于同一个应用对象和同一套 service 实现：

- [myt_cli/api.py](C:/code/myt/myt_cli/api.py)
- [myt_cli/client.py](C:/code/myt/myt_cli/client.py)
- [myt_cli/services/](C:/code/myt/myt_cli/services)

这样做的好处是：

- CLI 行为和 Python API 行为一致
- 后续修接口只需要改一处
- 更方便封装为第三方包

### 2. 盒子接口和 Android 接口的区别

项目里同时用了两类接口：

盒子级接口：

- 用于管理云机
- 地址形态通常是 `http://盒子IP:8000`
- 典型操作：
  - 列表
  - 启动
  - 关机
  - 删除
  - 导出
  - 导入

云机内部 Android 接口：

- 用于操作云机内部功能
- 当前主要用于 S5 代理
- 项目会自动根据云机信息推断访问地址

### 3. S5 代理端口选择

在你的真实环境里，S5 访问已确认优先通过：

- `盒子IP + 9082/tcp 对应的 HostPort`

例如：

- 盒子 IP：`10.0.103.227`
- 云机 `001` 的 `9082/tcp -> 30001`
- 则程序使用：`10.0.103.227:30001`

这部分逻辑位于：

- [s5_service.py](C:/code/myt/myt_cli/services/s5_service.py)

## 已知限制

### 1. 公开文档和真实盒子 Swagger 可能不完全一致

当前项目第一版基于公开文档实现。  
如果你盒子的真实 Swagger 在字段、参数名、返回结构上与文档不同，需要做定制化调整。

### 2. 备份名称不能自定义

严格按文档，`POST /android/export` 不支持你主动指定备份文件名。  
当前程序也遵循这一限制。

### 3. 恢复依赖盒子已有备份文件

当前恢复流程假设备份文件已经存在于盒子可下载的备份列表中。

### 4. 自动轮询尚未全面启用

当前部分操作直接依赖接口即时返回。  
如果后续你发现某些盒子操作是异步任务返回，可以继续把任务轮询接入：

- [polling.py](C:/code/myt/myt_cli/polling.py)

## 项目结构

```text
app.py
config.yaml
config.example.yaml
pyproject.toml
myt_cli/
  __init__.py
  __main__.py
  api.py
  cli.py
  client.py
  config.py
  exceptions.py
  logging_utils.py
  polling.py
  services/
    backup_service.py
    restore_service.py
    s5_service.py
    start_service.py
    vm_service.py
```

## 打包与发布

### 构建 wheel 和 sdist

```bash
python -m pip install build twine
python -m build
```

构建完成后会生成：

- `dist/*.whl`
- `dist/*.tar.gz`

### 上传到 PyPI

```bash
python -m twine upload dist/*
```

通常使用 PyPI API Token 上传：

- 用户名：`__token__`
- 密码：你的 `pypi-...` token

## 开发建议

如果你准备继续扩展，我建议下一个优先级是：

- 增加 `restart`
- 增加 `backups` 备份列表命令
- 增加任务轮询
- 增加更明确的异常类型导出
- 为 Python API 增加类型化返回对象

## License

MIT
