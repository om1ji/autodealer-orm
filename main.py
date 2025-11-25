"""Simple script that prints all rows from the BANK table."""

from __future__ import annotations

import logging
from pprint import pprint

from sqlalchemy import select

from autodealer import configure_database, session_scope

# Provide connection credentials directly for this script before models load.
configure_database(
    database=r"C:\Program Files (x86)\AutoDealer\AutoDealer\Database\AutoDealer061221.fdb",
    user="SYSDBA",
    password="masterkey",
    host="192.168.88.64",
    port=3050,
    charset="WIN1251",
)

from autodealer.domain.bank import Bank


def bank_to_dict(bank: Bank) -> dict[str, object]:
    """Serialize a Bank ORM object to plain data for pretty printing."""
    return {column.name: getattr(bank, column.name) for column in Bank.__table__.columns}


def fetch_all_banks() -> list[dict[str, object]]:
    with session_scope() as session:
        result = session.execute(select(Bank)).scalars().all()
        return [bank_to_dict(bank) for bank in result]


if __name__ == "__main__":
    try:
        pprint(fetch_all_banks())
    except Exception:
        logging.exception("Ошибка при чтении таблицы BANK")
