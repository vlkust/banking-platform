from datetime import datetime
from pathlib import Path

from exceptions import InvalidOperationError
from transaction_models import Transaction
from bank_models import Bank
from utils import (
                    logger,
                    numeric_value_validation,
                    string_value_validation,
                    ALLOWED_AUDIT_LEVEL_LIST,
                    ALLOWED_RISK_LEVEL_LIST,
                    DEFAULT_AUDIT_FILE,
                    DEFAULT_LARGE_AMOUNT_LIMIT,
                    DEFAULT_FREQUENT_OPERATION_LIMIT
)



class AuditLog:
    """Store audit events in memory and in a file."""

    def __init__(self, file_name: str = DEFAULT_AUDIT_FILE):
        """Initialize audit log.

        Args:
            file_name: File used to store audit events.
        """
        self.file_name = Path(file_name)
        self.records = []

        logger.info(
            f"AuditLog created: file_name={self.file_name}"
        )

    def add_record(self,
                    level: str,
                    event: str,
                    transaction: Transaction | None = None,
                    client_id: str | None = None,
                    details: str = "",
                ) -> dict:
        """Add an audit record to memory and file.

        Args:
            level: Audit importance level.
            event: Event name.
            transaction: Related transaction.
            client_id: Related client identifier.
            details: Additional event details.

        Returns:
            dict: Created audit record.
        """
        string_value_validation(level, ALLOWED_AUDIT_LEVEL_LIST, "audit_level")

        transaction_id = None
        if transaction is not None:
            transaction_id = transaction.transaction_id

        record = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "level": level,
            "event": event,
            "transaction_id": transaction_id,
            "client_id": client_id,
            "details": details,
        }

        self.records.append(record)

        with self.file_name.open("a", encoding="utf-8") as audit_file:
            audit_file.write(f"{record}\n")

        logger.info(
            f"Audit record added: level={level}, event={event}, "
            f"transaction_id={transaction_id}, client_id={client_id}"
        )

        return record

    def filter_records(self,
                        level: str | None = None,
                        event: str | None = None,
                        client_id: str | None = None,
                        transaction_id: str | None = None,
                    ) -> list:
        """Filter audit records by selected fields.

        Args:
            level: Audit level filter.
            event: Event filter.
            client_id: Client identifier filter.
            transaction_id: Transaction identifier filter.

        Returns:
            list: Matching audit records.
        """
        result = []

        for record in self.records:
            if level is not None and record["level"] != level:
                continue

            if event is not None and record["event"] != event:
                continue

            if client_id is not None and record["client_id"] != client_id:
                continue

            if transaction_id is not None:
                if record["transaction_id"] != transaction_id:
                    continue

            result.append(record)

        logger.info(
            f"Audit records filtered: count={len(result)}"
        )
        return result

    def get_error_statistics(self) -> dict:
        """Return audit error statistics.

        Returns:
            dict: Number of records for warning, error and critical levels.
        """
        statistics = {
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0,
        }

        for record in self.records:
            if record["level"] in statistics:
                statistics[record["level"]] += 1

        logger.info(
            f"Audit error statistics calculated: {statistics}"
        )
        return statistics


class RiskAnalyzer:
    """Analyze transactions and assign risk levels."""

    def __init__(self,
                bank: Bank,
                audit_log: AuditLog,
                large_amount_limit: float = DEFAULT_LARGE_AMOUNT_LIMIT,
                frequent_operation_limit: int = DEFAULT_FREQUENT_OPERATION_LIMIT,
            ):
        """Initialize risk analyzer.

        Args:
            bank: Bank object.
            audit_log: Audit log object.
            large_amount_limit: Amount considered large.
            frequent_operation_limit: Maximum allowed operations in time window.
        """
        self.bank = bank
        self.audit_log = audit_log
        self.large_amount_limit = large_amount_limit
        self.frequent_operation_limit = frequent_operation_limit
        self.transaction_history = []
        self.client_risk_profiles = {}

        numeric_value_validation(
            self.large_amount_limit,
            "large_amount_limit",
        )
        numeric_value_validation(
            self.frequent_operation_limit,
            "frequent_operation_limit",
        )

        logger.info(
            f"RiskAnalyzer created: large_amount_limit={self.large_amount_limit}, "
            f"frequent_operation_limit={self.frequent_operation_limit}"
        )

    def _is_night_operation(self, transaction: Transaction) -> bool:
        """Check whether transaction was created at night.

        Args:
            transaction: Transaction object.

        Returns:
            bool: True if transaction time is between 00:00 and 05:00.
        """
        transaction_time = datetime.fromisoformat(
            transaction.created_at
        )

        return 0 <= transaction_time.hour < 5

    def _is_new_recipient(self, transaction: Transaction) -> bool:
        """Check whether recipient is new for the transaction client.

        Args:
            transaction: Transaction object.

        Returns:
            bool: True if recipient is not linked to the client.
        """
        if transaction.to_account is None:
            return False

        if transaction.client_id is None:
            return False

        client = self.bank.bank_clients.get(transaction.client_id)
        if client is None:
            return False

        return transaction.to_account.account_id not in client.account_ids

    def _get_recent_client_transactions(self, transaction: Transaction) -> list:
        """Return recent transactions of the same client.

        Args:
            transaction: Transaction object.

        Returns:
            list: Previous client transactions.
        """
        if transaction.client_id is None:
            return []

        return [
            item
            for item in self.transaction_history
            if item.client_id == transaction.client_id
        ]

    def analyze_transaction(self, transaction: Transaction) -> dict:
        """Analyze one transaction and calculate its risk level.

        Args:
            transaction: Transaction object.

        Returns:
            dict: Risk level and detected reasons.
        """
        if not isinstance(transaction, Transaction):
            raise InvalidOperationError(
                "Only Transaction objects can be analyzed."
            )

        reasons = []

        if transaction.amount >= self.large_amount_limit:
            reasons.append("large_amount")

        recent_transactions = self._get_recent_client_transactions(transaction)

        if len(recent_transactions) >= self.frequent_operation_limit - 1:
            reasons.append("frequent_operations")

        if self._is_new_recipient(transaction):
            reasons.append("new_recipient")

        if self._is_night_operation(transaction):
            reasons.append("night_operation")

        if len(reasons) >= 2:
            risk_level = "high"
        elif len(reasons) == 1:
            risk_level = "medium"
        else:
            risk_level = "low"

        result = {
            "transaction_id": transaction.transaction_id,
            "client_id": transaction.client_id,
            "risk_level": risk_level,
            "reasons": reasons,
        }

        self.transaction_history.append(transaction)
        self._update_client_risk_profile(transaction, result)
        self._write_audit_result(transaction, result)

        logger.info(
            f"Transaction risk analyzed: id={transaction.transaction_id}, "
            f"risk_level={risk_level}, reasons={reasons}"
        )

        return result

    def _write_audit_result(self, transaction: Transaction, result: dict) -> None:
        """Write risk analysis result to audit log.

        Args:
            transaction: Transaction object.
            result: Risk analysis result.
        """
        level_by_risk = {
            "low": "INFO",
            "medium": "WARNING",
            "high": "CRITICAL",
        }

        audit_level = level_by_risk[result["risk_level"]]

        self.audit_log.add_record(
            level=audit_level,
            event="risk_analysis",
            transaction=transaction,
            client_id=transaction.client_id,
            details=(
                f"risk_level={result['risk_level']}; "
                f"reasons={result['reasons']}"
            ),
        )

    def _update_client_risk_profile(self, transaction: Transaction, result: dict) -> None:
        """Update accumulated client risk profile.

        Args:
            transaction: Transaction object.
            result: Risk analysis result.
        """
        client_id = transaction.client_id

        if client_id is None:
            return

        if client_id not in self.client_risk_profiles:
            self.client_risk_profiles[client_id] = {
                "client_id": client_id,
                "low_risk_count": 0,
                "medium_risk_count": 0,
                "high_risk_count": 0,
                "reasons": [],
                "risk_level": "low",
            }

        profile = self.client_risk_profiles[client_id]
        profile[f"{result['risk_level']}_risk_count"] += 1
        profile["reasons"].extend(result["reasons"])

        if result["risk_level"] == "high":
            profile["risk_level"] = "high"
        elif (
            result["risk_level"] == "medium"
            and profile["risk_level"] == "low"
        ):
            profile["risk_level"] = "medium"

    def block_dangerous_transaction(self, transaction: Transaction, risk_result: dict) -> bool:
        """Block transaction with high risk.

        Args:
            transaction: Transaction object.
            risk_result: Result of risk analysis.

        Returns:
            bool: True if transaction was blocked.
        """
        if risk_result["risk_level"] != "high":
            return False

        reason = (
            "Blocked by risk analyzer: "
            + ", ".join(risk_result["reasons"])
        )

        transaction.mark_failed(reason)

        self.audit_log.add_record(
            level="CRITICAL",
            event="transaction_blocked",
            transaction=transaction,
            client_id=transaction.client_id,
            details=reason,
        )

        logger.warning(
            f"Dangerous transaction blocked: "
            f"id={transaction.transaction_id}, reason={reason}"
        )

        return True

    def get_client_risk_profile(self, client_id: str) -> dict:
        """Return risk profile for a client.

        Args:
            client_id: Client identifier.

        Returns:
            dict: Client risk profile.
        """
        return self.client_risk_profiles.get(
            client_id,
            {
                "client_id": client_id,
                "low_risk_count": 0,
                "medium_risk_count": 0,
                "high_risk_count": 0,
                "reasons": [],
                "risk_level": "low",
            },
        )

    def get_suspicious_transactions(self) -> list:
        """Return transactions with medium or high risk.

        Returns:
            list: Suspicious transaction records.
        """
        return [
            record
            for record in self.audit_log.records
            if (
                record["event"] == "risk_analysis"
                and record["level"] in ["WARNING", "CRITICAL"]
            )
        ]