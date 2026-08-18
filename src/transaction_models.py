from datetime import datetime
from typing import Optional
from uuid import uuid4
from typing import TYPE_CHECKING, Optional

from account_models import BankAccount, PremiumAccount
from bank_models import Bank
from exceptions import InvalidOperationError
from utils import (
                    logger,
                    generate_id,
                    numeric_value_validation,
                    string_value_validation,
                    ALLOWED_TRANSACTION_TYPE_LIST,
                    ALLOWED_TRANSACTION_STATUS_LIST,
                    DEFAULT_EXCHANGE_RATES
)

if TYPE_CHECKING:
    from audit_models import RiskAnalyzer

class Transaction:
    def __init__(self, 
                transaction_id: str | None = None,
                transaction_type: str = "", 
                transaction_status: str = "pending", 
                amount: float = 0.0, 
                currency: str = "", 
                commission: float = 0.0, 
                from_account: Optional[BankAccount] = None, 
                to_account: Optional[BankAccount] = None, 
                client_id: Optional[str] = None,
                scheduled_at: str | None = None,
                max_retries: int = 3
                ):
        """Initialize transaction.

        Args:
            transaction_id: Unique transaction identifier
            transaction_type: Transaction type.
            amount: Transaction amount.
            currency: Transaction currency.
            from_account: Source account.
            to_account: Destination account.
            commission: Transaction commission.
            client_id: Client identifier.
        """
        self.transaction_id = generate_id(transaction_id, "Transaction ID")
        self.transaction_type = transaction_type
        self.transaction_status = transaction_status
        self.from_account = from_account
        self.to_account = to_account
        self.amount = amount
        self.currency = currency
        self.commission = commission
        self.client_id = client_id

        self.scheduled_at = scheduled_at
        self.max_retries = max_retries
        self.retry_count = 0

        self.failure_reason = None
        self.created_at = datetime.now().isoformat(timespec="seconds")
        self.updated_at = self.created_at
        self.processed_at = None

        self._validate()

        logger.info(
            f"Transaction created: id={self.transaction_id}, type={self.transaction_type}, "
            f"amount={self.amount}, currency={self.currency}, status={self.transaction_status}, "
            f"scheduled_at={self.scheduled_at}, max_retries={self.max_retries}"
        )

    def _validate(self) -> None:
        """Validate transaction data."""
        string_value_validation(self.transaction_type, ALLOWED_TRANSACTION_TYPE_LIST, "transaction_type")
        string_value_validation(self.transaction_status, ALLOWED_TRANSACTION_STATUS_LIST, "transaction_status")
        numeric_value_validation(self.amount, "amount")
        numeric_value_validation(self.commission, "commission")

        if self.from_account is not None and not isinstance(self.from_account, BankAccount):
            logger.error(f"Invalid from_account type: {type(self.from_account).__name__}")
            raise InvalidOperationError("from_account must be a BankAccount instance.")

        if self.to_account is not None and not isinstance(self.to_account, BankAccount):
            logger.error(f"Invalid to_account type: {type(self.to_account).__name__}")
            raise InvalidOperationError("to_account must be a BankAccount instance.")

    def mark_completed(self) -> None:
        """Mark transaction as completed."""
        self.transaction_status = "completed"
        self.processed_at = datetime.now().isoformat(timespec="seconds")
        self.updated_at = self.processed_at
        logger.info(f"Transaction completed: id={self.transaction_id}")

    def mark_failed(self, reason: str) -> None:
        """Mark transaction as failed."""
        self.transaction_status = "failed"
        self.failure_reason = reason
        self.updated_at = datetime.now().isoformat(timespec="seconds")
        logger.error(f"Transaction failed: id={self.transaction_id}, reason={reason}")

    def mark_cancelled(self) -> None:
        """Mark transaction as cancelled."""
        self.transaction_status = "cancelled"
        self.updated_at = datetime.now().isoformat(timespec="seconds")
        logger.info(f"Transaction cancelled: id={self.transaction_id}")

    def is_ready_to_execute(self, current_time: str | None = None) -> bool:
        """Check if scheduled transaction execution time has arrived.

        Args:
            current_time: Time to compare against in ISO format. Defaults to current time.

        Returns:
            bool: True if transaction can be executed now.
        """
        if self.scheduled_at is None:
            return True

        check_time = current_time or datetime.now().isoformat(timespec="seconds")
        return self.scheduled_at <= check_time

    def get_transaction_info(self) -> dict:
        """Return structured transaction information.

        Returns:
            dict: Transaction data.
        """
        return {
            "transaction_id": self.transaction_id,
            "transaction_type": self.transaction_type,
            "amount": self.amount,
            "currency": self.currency,
            "from_account_id": getattr(self.from_account, "account_id", None),
            "to_account_id": getattr(self.to_account, "account_id", None),
            "commission": self.commission,
            "client_id": self.client_id,
            "status": self.transaction_status,
            "failure_reason": self.failure_reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "processed_at": self.processed_at,
        }

    def __str__(self) -> str:
        """Return readable transaction description.

        Returns:
            str: String representation.
        """
        return (
            f"Transaction | ID: {self.transaction_id} | Type: {self.transaction_type} | "
            f"Amount: {self.amount} {self.currency} | Status: {self.transaction_status}"
        )


class TransactionQueue:
    def __init__(self):
        """Initialize transaction queue."""
        self.transactions = []
        self.priority_transactions = []

        logger.info("TransactionQueue created")

    def add_transaction(self, transaction: Transaction, priority: bool = False, scheduled_at: str | None = None) -> None:
        """Add transaction to queue.

        Args:
            transaction: Transaction object.
            priority: Priority flag.
        """
        if not isinstance(transaction, Transaction):
            logger.error(f"Invalid transaction type: {type(transaction).__name__}")
            raise InvalidOperationError("Only Transaction objects can be added to queue.")

        if scheduled_at is not None:
            transaction.scheduled_at = scheduled_at

        if priority:
            self.priority_transactions.append(transaction)
            logger.info(
                f"Priority transaction added to queue: id={transaction.transaction_id}"
            )
        else:
            self.transactions.append(transaction)
            logger.info(f"Transaction added to queue: id={transaction.transaction_id}")

    def get_ready_transactions(self, current_time: str | None = None) -> tuple[list[Transaction], list[Transaction]]:
        """Split queued transactions into ready-to-process and future-scheduled.

        Args:
            current_time: Time to compare against in ISO format.

        Returns:
            tuple: (ready_priority + ready_normal, remaining_scheduled)
        """
        ready_priority = []
        remaining_priority = []
        for t in self.priority_transactions:
            if t.is_ready_to_execute(current_time):
                ready_priority.append(t)
            else:
                remaining_priority.append(t)

        ready_normal = []
        remaining_normal = []
        for t in self.transactions:
            if t.is_ready_to_execute(current_time):
                ready_normal.append(t)
            else:
                remaining_normal.append(t)

        self.priority_transactions = remaining_priority
        self.transactions = remaining_normal

        ready = ready_priority + ready_normal
        return ready

    def cancel_transaction(self, transaction_id: str) -> bool:
        """Cancel transaction by id.

        Args:
            transaction_id: Transaction identifier.

        Returns:
            bool: Cancellation result.
        """
        for queue in [self.priority_transactions, self.transactions]:
            for transaction in queue:
                if transaction.transaction_id == transaction_id:
                    if transaction.transaction_status in ["pending", "processing"]:
                        transaction.mark_cancelled()
                        queue.remove(transaction)
                        logger.info(f"Transaction cancelled in queue: id={transaction_id}")
                        return True
                    else:
                        logger.warning(
                            f"Cannot cancel transaction: id={transaction_id}, transaction_status={transaction.transaction_status}"
                        )
                        return False

        logger.warning(f"Transaction not found in queue: id={transaction_id}")
        return False

    def get_queue_info(self) -> dict:
        """Return queue information.

        Returns:
            dict: Queue data.
        """
        return {
            "pending_count": len(self.transactions),
            "priority_count": len(self.priority_transactions),
            "pending_ids": [t.transaction_id for t in self.transactions],
            "priority_ids": [t.transaction_id for t in self.priority_transactions],
        }


class TransactionProcessor:
    def __init__(self, bank: Bank, external_transfer_commission: float = 0.00, exchange_rates: dict | None = None, risk_analyzer: Optional["RiskAnalyzer"] = None, max_retries: int = 3):
        """Initialize transaction processor.

        Args:
            bank: Bank object.
            external_transfer_commission: External transfer commission rate.
            exchange_rates: Currency exchange rates.
            risk_analyzer: Optional RiskAnalyzer instance.
            max_retries: Default retry limit for transactions.
        """
        self.bank = bank
        self.external_transfer_commission = external_transfer_commission
        self.exchange_rates = exchange_rates or DEFAULT_EXCHANGE_RATES
        self.risk_analyzer: Optional["RiskAnalyzer"] = risk_analyzer
        self.max_retries = max_retries

        self.queue = TransactionQueue()
        self.processed_transactions = []
        self.failed_transactions = []

        logger.info(
            f"TransactionProcessor created: external_commission={self.external_transfer_commission}, "
            f"max_retries={self.max_retries}"
        )

    def _check_account_allowed(self, account: BankAccount, transaction: Transaction) -> bool:
        """Check if account can participate in transaction.

        Args:
            account: Account to check.
            transaction: Transaction object.

        Returns:
            bool: Permission result.
        """
        if account is None:
            return True

        if account.status == "frozen":
            transaction.mark_failed(f"Account frozen: {account.account_id}")
            logger.error(f"Transaction blocked: frozen account {account.account_id}")
            return False

        if account.status == "closed":
            transaction.mark_failed(f"Account closed: {account.account_id}")
            logger.error(f"Transaction blocked: closed account {account.account_id}")
            return False

        return True

    def _calculate_commission(self, transaction: Transaction) -> float:
        """Calculate commission for transaction.

        Args:
            transaction: Transaction object.

        Returns:
            float: Commission amount.
        """
        if transaction.transaction_type == "external_transfer":
            return transaction.amount * self.external_transfer_commission
        return transaction.commission

    def _apply_commission(self, transaction: Transaction) -> None:
        """Apply commission to source account.

        Args:
            transaction: Transaction object.
        """
        commission = self._calculate_commission(transaction)
        if commission > 0 and transaction.from_account is not None:
            commission_in_acc_curr = self._convert_currency(
                amount=commission,
                from_currency=transaction.currency,
                to_currency=transaction.from_account.currency,
            )
            transaction.from_account.withdraw(commission_in_acc_curr)
            logger.info(
                f"Commission applied: transaction={transaction.transaction_id}, "
                f"amount={commission_in_acc_curr} {transaction.from_account.currency}"
            )

    def _convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert amount between currencies using bank rates.

        Args:
            amount: Amount to convert.
            from_currency: Source currency.
            to_currency: Target currency.

        Returns:
            float: Converted amount.
        """
        if from_currency not in self.exchange_rates:
            raise InvalidOperationError(f"Unsupported source currency: {from_currency}")
        
        if to_currency not in self.exchange_rates:
            raise InvalidOperationError(f"Unsupported target currency: {to_currency}")
        
        if from_currency == to_currency:
            return amount

        amount_in_rub = amount * self.exchange_rates[from_currency]
        converted_amount = amount_in_rub / self.exchange_rates[to_currency]

        logger.info(
            f"Currency converted: {amount} {from_currency} -> "
            f"{converted_amount:.2f} {to_currency}"
        )
        return converted_amount

    def process_transaction(self, transaction: Transaction) -> bool:
        """Process single transaction.

        Args:
            transaction: Transaction object.

        Returns:
            bool: Processing result.
        """
        logger.info(
            f"Processing transaction: id={transaction.transaction_id}, "
            f"attempt={transaction.retry_count + 1}/{transaction.max_retries}"
        )
        transaction.transaction_status = "processing"
        transaction.updated_at = datetime.now().isoformat(timespec="seconds")

        if self.risk_analyzer is not None:
            risk_result = self.risk_analyzer.analyze_transaction(transaction)
            if self.risk_analyzer.block_dangerous_transaction(
                transaction, risk_result
            ):
                self.failed_transactions.append(transaction)
                logger.warning(
                    f"Transaction blocked by risk analyzer: id={transaction.transaction_id}"
                )
                return False

        if not self._check_account_allowed(transaction.from_account, transaction):
            self._handle_failure(transaction, transaction.failure_reason or "Account not allowed")
            return False

        if not self._check_account_allowed(transaction.to_account, transaction):
            self._handle_failure(transaction, transaction.failure_reason or "Account not allowed")
            return False

        try:
            if transaction.transaction_type == "deposit":
                if transaction.to_account is not None:
                    deposit_amount = self._convert_currency(
                        amount=transaction.amount,
                        from_currency=transaction.currency,
                        to_currency=transaction.to_account.currency,
                    )
                    transaction.to_account.deposit(deposit_amount)

            elif transaction.transaction_type == "withdrawal":
                if transaction.from_account is not None:
                    withdraw_amount = self._convert_currency(
                        amount=transaction.amount,
                        from_currency=transaction.currency,
                        to_currency=transaction.from_account.currency,
                    )
                    transaction.from_account.withdraw(withdraw_amount)

            elif transaction.transaction_type in ["transfer", "external_transfer"]:
                if transaction.from_account is not None and transaction.to_account is not None:
                    withdraw_amount = self._convert_currency(
                        amount=transaction.amount,
                        from_currency=transaction.currency,
                        to_currency=transaction.from_account.currency,
                    )
                    deposit_amount = self._convert_currency(
                        amount=transaction.amount,
                        from_currency=transaction.currency,
                        to_currency=transaction.to_account.currency,
                    )

                    transaction.from_account.withdraw(withdraw_amount)

                    try:
                        transaction.to_account.deposit(deposit_amount)
                    except Exception as deposit_error:
                        transaction.from_account.deposit(withdraw_amount)
                        raise deposit_error

                    self._apply_commission(transaction)

            else:
                self._handle_failure(transaction, f"Unknown transaction type: {transaction.transaction_type}")
                return False

            transaction.mark_completed()
            self.processed_transactions.append(transaction)
            logger.info(
                f"Transaction processed successfully: id={transaction.transaction_id}"
            )
            return True

        except Exception as error:
            self._handle_failure(transaction, str(error))
            return False

    def _handle_failure(self, transaction: Transaction, reason: str) -> None:
        """Handle transaction processing error with retry attempt tracking.

        Args:
            transaction: Failed transaction object.
            reason: Error description.
        """
        transaction.retry_count += 1
        transaction.updated_at = datetime.now().isoformat(timespec="seconds")

        if transaction.retry_count < transaction.max_retries:
            transaction.transaction_status = "pending"
            transaction.failure_reason = (
                f"Attempt {transaction.retry_count} failed: {reason}"
            )
            logger.warning(
                f"Transaction attempt failed, scheduled for retry: id={transaction.transaction_id}, "
                f"attempt={transaction.retry_count}/{transaction.max_retries}, error={reason}"
            )
        else:
            transaction.mark_failed(
                f"Exceeded max retries ({transaction.max_retries}). Last error: {reason}"
            )
            self.failed_transactions.append(transaction)
            logger.error(
                f"Transaction permanently failed: id={transaction.transaction_id}, "
                f"retries={transaction.retry_count}, reason={transaction.failure_reason}"
            )

    def process_queue(self, current_time: str | None = None) -> dict:
        """Process ready transactions from queue with retry support.

        Args:
            current_time: Optional ISO timestamp to filter scheduled transactions.

        Returns:
            dict: Processing results summary.
        """
        logger.info("Processing transaction queue started")

        ready_transactions = self.queue.get_ready_transactions(current_time)

        success_count = 0
        retry_count = 0
        failed_count = 0

        for transaction in ready_transactions:
            if self.process_transaction(transaction):
                success_count += 1
            else:
                if transaction.transaction_status == "pending":
                    self.queue.add_transaction(transaction, priority=False)
                    retry_count += 1
                else:
                    failed_count += 1

        result = {
            "processed": success_count,
            "retrying": retry_count,
            "failed": failed_count,
            "remaining_in_queue": len(self.queue.transactions) + len(self.queue.priority_transactions),
            "total_executed": len(ready_transactions),
        }

        logger.info(
            f"Queue processing finished: processed={result['processed']}, "
            f"retrying={result['retrying']}, failed={result['failed']}, "
            f"remaining_in_queue={result['remaining_in_queue']}"
        )
        return result

    def get_processor_info(self) -> dict:
        """Return processor information.

        Returns:
            dict: Processor data.
        """
        return {
            "processed_count": len(self.processed_transactions),
            "failed_count": len(self.failed_transactions),
            "queue_info": self.queue.get_queue_info(),
        }
