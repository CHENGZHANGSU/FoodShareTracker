from pathlib import Path

from util.admin_utils import backup_data


def test_backup_skips_absent_daily_order_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    inventory_path = tmp_path / "inventory.json"
    inventory_path.write_text('{"inventory": []}', encoding="utf-8")
    (tmp_path / "assets" / "orders").mkdir(parents=True)
    backup_dir = tmp_path / "backups"

    assert backup_data(str(inventory_path), str(backup_dir)) is True
    assert len(list(backup_dir.glob("inventory_backup_*.json"))) == 1
    assert list(backup_dir.glob("order_backup_*.json")) == []


def test_backup_reports_missing_inventory_file(tmp_path: Path) -> None:
    assert backup_data(
        str(tmp_path / "missing.json"),
        str(tmp_path / "backups"),
    ) is False
