import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt

from bank_models import Bank
from transaction_models import Transaction
from audit_models import AuditLog
from utils import logger


class ReportBuilder:
    """Build text, JSON, CSV and chart reports."""

    def __init__(
        self,
        bank: Bank,
        transactions: list[Transaction],
        audit_log: AuditLog,
        processor,
    ):
        """Initialize report builder.

        Args:
            bank: Bank object.
            transactions: All project transactions.
            audit_log: Audit log object.
            processor: Transaction processor.
        """
        self.bank = bank
        self.transactions = transactions
        self.audit_log = audit_log
        self.processor = processor

        logger.info("ReportBuilder created")

    def build_client_report(self, client_id: str) -> dict:
        """Build report for one client.

        Args:
            client_id: Client identifier.

        Returns:
            dict: Client report.
        """
        client = self.bank.bank_clients.get(client_id)

        if client is None:
            logger.error(
                f"Client report failed: client_id={client_id}"
            )
            return {}

        accounts = []
        total_balance = 0.0

        for account_id in client.account_ids:
            account = self.bank.bank_accounts.get(account_id)

            if account is not None:
                accounts.append(account.get_account_info())
                total_balance += account.balance

        client_transactions = [
            transaction.get_transaction_info()
            for transaction in self.transactions
            if transaction.client_id == client_id
        ]

        report = {
            "client": client.get_client_info(),
            "accounts": accounts,
            "total_balance": total_balance,
            "transactions": client_transactions,
        }

        logger.info(
            f"Client report built: client_id={client_id}"
        )

        return report

    def build_bank_report(self) -> dict:
        """Build general bank report.

        Returns:
            dict: Bank report.
        """
        ranking = self.bank.get_clients_ranking()

        status_statistics = {
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        }

        type_statistics = {}

        for transaction in self.transactions:
            status = transaction.transaction_status
            transaction_type = transaction.transaction_type

            if status in status_statistics:
                status_statistics[status] += 1

            type_statistics[transaction_type] = (
                type_statistics.get(transaction_type, 0) + 1
            )

        report = {
            "total_clients": len(self.bank.bank_clients),
            "total_accounts": len(self.bank.bank_accounts),
            "total_balance": self.bank.get_total_balance(),
            "top_clients": ranking[:3],
            "transaction_count": len(self.transactions),
            "transaction_status_statistics": status_statistics,
            "transaction_type_statistics": type_statistics,
            "processor_info": self.processor.get_processor_info(),
        }

        logger.info("Bank report built")

        return report

    def build_risk_report(self) -> dict:
        """Build risk and audit report.

        Returns:
            dict: Risk report.
        """
        suspicious_records = [
            record
            for record in self.audit_log.records
            if (
                record["event"] == "risk_analysis"
                and record["level"] in ["WARNING", "CRITICAL"]
            )
        ]

        blocked_records = [
            record
            for record in self.audit_log.records
            if record["event"] == "transaction_blocked"
        ]

        client_risk_profiles = {}

        for client_id in self.bank.bank_clients:
            profile = self.audit_log.filter_records(
                client_id=client_id,
                event="risk_analysis",
            )

            client_risk_profiles[client_id] = profile

        report = {
            "suspicious_operations": suspicious_records,
            "blocked_operations": blocked_records,
            "client_risk_profiles": client_risk_profiles,
            "audit_error_statistics": self.audit_log.get_error_statistics(),
        }

        logger.info("Risk report built")

        return report

    def build_text_report(self) -> str:
        """Build a short text report.

        Returns:
            str: Text representation of the system report.
        """
        bank_report = self.build_bank_report()
        risk_report = self.build_risk_report()

        lines = [
            "BANKING PLATFORM REPORT",
            "",
            "BANK STATISTICS",
            f"Clients: {bank_report['total_clients']}",
            f"Accounts: {bank_report['total_accounts']}",
            f"Total balance: {bank_report['total_balance']:.2f}",
            f"Transactions: {bank_report['transaction_count']}",
            "",
            "TOP CLIENTS",
        ]

        for position, client in enumerate(
            bank_report["top_clients"],
            start=1,
        ):
            lines.append(
                f"{position}. {client['full_name']} - "
                f"{client['total_balance']:.2f}"
            )

        lines.extend(
            [
                "",
                "RISK STATISTICS",
                (
                    "Suspicious operations: "
                    f"{len(risk_report['suspicious_operations'])}"
                ),
                (
                    "Blocked operations: "
                    f"{len(risk_report['blocked_operations'])}"
                ),
                (
                    "Audit statistics: "
                    f"{risk_report['audit_error_statistics']}"
                ),
            ]
        )

        report = "\n".join(lines)

        logger.info("Text report built")

        return report

    def export_to_json(
        self,
        report: dict,
        file_name: str,
    ) -> None:
        """Export report to JSON file.

        Args:
            report: Report dictionary.
            file_name: Output file name.
        """
        output_path = Path(file_name)

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as json_file:
            json.dump(
                report,
                json_file,
                ensure_ascii=False,
                indent=4,
            )

        logger.info(
            f"JSON report exported: file={output_path}"
        )

    def export_to_csv(
        self,
        rows: list[dict],
        file_name: str,
    ) -> None:
        """Export list of dictionaries to CSV file.

        Args:
            rows: Report rows.
            file_name: Output file name.
        """
        output_path = Path(file_name)

        if not rows:
            logger.warning(
                f"CSV report skipped because rows are empty: file={output_path}"
            )
            return

        fieldnames = set()

        for row in rows:
            fieldnames.update(row.keys())

        fieldnames = sorted(fieldnames)

        with output_path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=fieldnames,
            )
            writer.writeheader()

            for row in rows:
                writer.writerow(
                    {
                        key: row.get(key, "")
                        for key in fieldnames
                    }
                )

        logger.info(
            f"CSV report exported: file={output_path}"
        )

    def save_charts(self, output_directory: str = "reports/charts") -> None:
        """Build and save all project charts.

        Args:
            output_directory: Directory for chart files.
        """
        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)

        self._save_transaction_status_pie_chart(output_path)
        self._save_client_balance_bar_chart(output_path)
        self._save_balance_movement_chart(output_path)

        logger.info(
            f"Charts saved: directory={output_path}"
        )

    def _save_transaction_status_pie_chart(
        self,
        output_path: Path,
    ) -> None:
        """Save transaction status pie chart.

        Args:
            output_path: Chart output directory.
        """
        status_statistics = {}

        for transaction in self.transactions:
            status = transaction.transaction_status
            status_statistics[status] = (
                status_statistics.get(status, 0) + 1
            )

        if not status_statistics:
            return

        plt.figure(figsize=(7, 7))
        plt.pie(
            status_statistics.values(),
            labels=status_statistics.keys(),
            autopct="%1.1f%%",
        )
        plt.title("Transaction Statuses")
        plt.tight_layout()
        plt.savefig(
            output_path / "transaction_statuses.png",
            dpi=150,
        )
        plt.close()

    def _save_client_balance_bar_chart(
        self,
        output_path: Path,
    ) -> None:
        """Save client balance bar chart.

        Args:
            output_path: Chart output directory.
        """
        ranking = self.bank.get_clients_ranking()

        names = [
            client["full_name"]
            for client in ranking
        ]
        balances = [
            client["total_balance"]
            for client in ranking
        ]

        if not names:
            return

        plt.figure(figsize=(10, 6))
        plt.bar(names, balances)
        plt.title("Client Balances")
        plt.xlabel("Clients")
        plt.ylabel("Balance")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        plt.savefig(
            output_path / "client_balances.png",
            dpi=150,
        )
        plt.close()

    def _save_balance_movement_chart(
        self,
        output_path: Path,
    ) -> None:
        """Save balance movement line chart.

        Args:
            output_path: Chart output directory.
        """
        movement = 0.0
        movements = [movement]

        for transaction in self.transactions:
            if transaction.transaction_status != "completed":
                continue

            if transaction.transaction_type == "deposit":
                movement += transaction.amount

            elif transaction.transaction_type == "withdrawal":
                movement -= transaction.amount

            elif transaction.transaction_type in [
                "transfer",
                "external_transfer",
            ]:
                commission = transaction.commission
                movement -= commission

            movements.append(movement)

        if len(movements) < 2:
            return

        plt.figure(figsize=(10, 6))
        plt.plot(
            range(len(movements)),
            movements,
            marker="o",
        )
        plt.title("Balance Movement")
        plt.xlabel("Completed transaction number")
        plt.ylabel("Balance movement")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(
            output_path / "balance_movement.png",
            dpi=150,
        )
        plt.close()