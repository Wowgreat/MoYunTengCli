import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Optional

from myt_cli.api import create_app_from_path
from myt_cli.exceptions import MytCliError
from myt_cli.logging_utils import configure_logging


LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myt-cli")
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List VMs")

    status_parser = subparsers.add_parser("status", help="Show VM status")
    status_parser.add_argument("--name", required=True, help="VM name")

    start_parser = subparsers.add_parser("start", help="Start a VM")
    start_parser.add_argument("--name", required=True, help="VM name")

    stop_parser = subparsers.add_parser("stop", help="Stop a VM")
    stop_parser.add_argument("--name", required=True, help="VM name")

    delete_parser = subparsers.add_parser("delete", help="Delete a VM")
    delete_parser.add_argument("--name", required=True, help="VM name")

    s5_status_parser = subparsers.add_parser("s5-status", help="Query S5 proxy status for a VM")
    s5_status_parser.add_argument("--name", required=True, help="VM name")

    s5_set_parser = subparsers.add_parser("s5-set", help="Configure S5 proxy for a VM")
    s5_set_parser.add_argument("--name", required=True, help="VM name")
    s5_set_parser.add_argument("--ip", "--proxy-ip", dest="proxy_ip", required=True, help="SOCKS5 server IP")
    s5_set_parser.add_argument("--port", "--proxy-port", dest="proxy_port", required=True, type=int, help="SOCKS5 server port")
    s5_set_parser.add_argument("--user", "--proxy-user", dest="proxy_user", required=True, help="SOCKS5 username")
    s5_set_parser.add_argument("--password", "--proxy-password", dest="proxy_password", required=True, help="SOCKS5 password")
    s5_set_parser.add_argument("--type", "--proxy-type", dest="proxy_type", type=int, choices=[1, 2], default=2, help="1 local DNS, 2 server DNS")

    s5_stop_parser = subparsers.add_parser("s5-stop", help="Stop S5 proxy for a VM")
    s5_stop_parser.add_argument("--name", required=True, help="VM name")

    backup_parser = subparsers.add_parser("backup", help="Export a VM backup archive")
    backup_parser.add_argument("--name", required=True, help="VM name")

    subparsers.add_parser("backup-all", help="Export backup archives for all occupied VM slots")

    backups_parser = subparsers.add_parser("backups", help="List backup archives")
    backups_parser.add_argument("--name", help="Filter by backup archive file name")

    restore_parser = subparsers.add_parser("restore", help="Restore a VM from a backup archive on the box")
    restore_parser.add_argument("--backup", required=True, help="Backup archive file name")
    restore_parser.add_argument("--index-num", type=int, help="Target indexNum for the imported VM; omit to auto-pick")
    restore_parser.add_argument("--target", help="Target VM name after import")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    app = create_app_from_path(_resolve_config_path(args.config))
    config = app.config
    configure_logging(config.logging)

    try:
        if args.command == "list":
            result = app.list_vms()
        elif args.command == "status":
            result = app.get_vm_status(args.name)
        elif args.command == "start":
            result = app.start_vm(args.name)
        elif args.command == "stop":
            result = app.stop_vm(args.name)
        elif args.command == "delete":
            result = app.delete_vm(args.name)
        elif args.command == "s5-status":
            result = app.get_s5_status(args.name)
        elif args.command == "s5-set":
            result = app.set_s5_proxy(
                name=args.name,
                proxy_ip=args.proxy_ip,
                proxy_port=args.proxy_port,
                proxy_user=args.proxy_user,
                proxy_password=args.proxy_password,
                proxy_type=args.proxy_type,
            )
        elif args.command == "s5-stop":
            result = app.stop_s5_proxy(args.name)
        elif args.command == "backup":
            result = app.backup_vm(args.name)
        elif args.command == "backup-all":
            result = app.backup_all_vms()
        elif args.command == "backups":
            result = {"backups": app.list_backups(args.name)}
        elif args.command == "restore":
            result = app.restore_backup(
                backup_name=args.backup,
                index_num=args.index_num,
                target_name=args.target,
            )
        else:
            parser.error(f"Unsupported command: {args.command}")
            return 2
    except MytCliError as exc:
        LOGGER.error("%s", exc)
        print(f"[FAIL] {exc}")
        return 1

    print(_format_output(result))
    return 0


def _format_output(result: object) -> str:
    if isinstance(result, dict):
        if {"total", "success_count", "failure_count", "skipped_count", "successes", "failures"}.issubset(result.keys()):
            return _format_backup_all_result(result)
        if "backups" in result and isinstance(result["backups"], list):
            return _format_backup_list(result["backups"])
        if {"vm_name", "vm_id", "status", "export_name"}.issubset(result.keys()):
            return _format_backup_result(result)
        if "proxy" in result and "vm_name" in result:
            return _format_s5_status(result)
        if {"proxy_ip", "proxy_port"}.issubset(result.keys()):
            return _format_s5_set(result)
        if result.get("message") == "stop success" and "vm_name" in result:
            return _format_s5_stop(result)
    return json.dumps(result, ensure_ascii=False, indent=2)


def _resolve_config_path(config_arg: str, *, cwd: Optional[Path] = None, package_dir: Optional[Path] = None) -> Path:
    candidate = Path(config_arg)
    if candidate.is_absolute():
        return candidate

    current_dir = cwd or Path.cwd()
    current_path = current_dir / candidate
    if current_path.exists():
        return current_path

    fallback_dir = package_dir or Path(__file__).resolve().parent.parent
    return fallback_dir / candidate


def _format_backup_result(result: Dict[str, object]) -> str:
    lines = [
        "[OK] Backup completed",
        f"VM: {result.get('vm_name')}",
        f"VM ID: {result.get('vm_id')}",
        f"VM Status: {result.get('status')}",
        f"Backup: {result.get('export_name')}",
    ]
    return "\n".join(lines)


def _format_backup_all_result(result: Dict[str, object]) -> str:
    successes = result.get("successes", [])
    failures = result.get("failures", [])
    if not isinstance(successes, list):
        successes = []
    if not isinstance(failures, list):
        failures = []

    lines = [
        "[OK] Batch backup completed",
        f"Total: {result.get('total')}",
        f"Success: {result.get('success_count')}",
        f"Failed: {result.get('failure_count')}",
        f"Skipped: {result.get('skipped_count')}",
    ]

    if successes:
        lines.append("Successful Backups:")
        for item in successes:
            if isinstance(item, dict):
                lines.append(f"- {item.get('vm_name')} -> {item.get('export_name')}")

    if failures:
        lines.append("Failed Backups:")
        for item in failures:
            if isinstance(item, dict):
                lines.append(f"- {item.get('vm_name')}: {item.get('error')}")

    return "\n".join(lines)


def _format_backup_list(result: list[Dict[str, object]]) -> str:
    if not result:
        return "Backup Archives:\n-"

    lines = ["Backup Archives:"]
    for item in result:
        created = item.get("created")
        size = item.get("size")
        suffix_parts = []
        if created:
            suffix_parts.append(f"created={created}")
        if size:
            suffix_parts.append(f"size={size}")
        suffix = f" ({', '.join(suffix_parts)})" if suffix_parts else ""
        lines.append(f"- {item.get('name')}{suffix}")
    return "\n".join(lines)


def _format_s5_status(result: Dict[str, object]) -> str:
    proxy = result.get("proxy", {})
    if not isinstance(proxy, dict):
        proxy = {}
    lines = [
        f"VM: {result.get('vm_name')}",
        f"Android API: {result.get('android_api_host')}:{result.get('android_api_port')}",
        f"S5状态: {proxy.get('statusText', '-')}",
        f"代理地址: {proxy.get('addr', '-')}",
        f"代理模式: {proxy.get('type', '-')}",
        f"消息: {result.get('message', '-')}",
    ]
    return "\n".join(lines)


def _format_s5_set(result: Dict[str, object]) -> str:
    lines = [
        f"[OK] S5 已设置到云机 {result.get('vm_name')}",
        f"Android API: {result.get('android_api_host')}:{result.get('android_api_port')}",
        f"代理地址: {result.get('proxy_ip')}:{result.get('proxy_port')}",
        f"代理模式: {result.get('proxy_type')}",
        f"消息: {result.get('message', '-')}",
    ]
    return "\n".join(lines)


def _format_s5_stop(result: Dict[str, object]) -> str:
    lines = [
        f"[OK] S5 已停止: {result.get('vm_name')}",
        f"Android API: {result.get('android_api_host')}:{result.get('android_api_port')}",
        f"消息: {result.get('message', '-')}",
    ]
    return "\n".join(lines)
