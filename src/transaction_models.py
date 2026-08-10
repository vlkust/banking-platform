from datetime import datetime
from typing import Optional
from uuid import uuid4

from account_models import BankAccount, PremiumAccount
from bank_models import Bank
from exceptions import InvalidOperationError
from utils import (
                    logger,
                    generate_id,
                    numeric_value_validation,
                    string_value_validation,
                    ALLOWED_TRANSACTION_TYPE_LIST,
                    ALLOWED_TRANSACTION_STATUS_LIST
)


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
                client_id: Optional[str] = None
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

        self.failure_reason = None
        self.created_at = datetime.now().isoformat(timespec="seconds")
        self.updated_at = self.created_at
        self.processed_at = None

        self._validate()

        logger.info(
            f"Transaction created: id={self.transaction_id}, type={self.transaction_type}, "
            f"amount={self.amount}, currency={self.currency}, status={self.transaction_status}"
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

    def add_transaction(self, transaction: Transaction, priority: bool = False) -> None:
        """Add transaction to queue.

        Args:
            transaction: Transaction object.
            priority: Priority flag.
        """
        if not isinstance(transaction, Transaction):
            logger.error(f"Invalid transaction type: {type(transaction).__name__}")
            raise InvalidOperationError("Only Transaction objects can be added to queue.")

        if priority:
            self.priority_transactions.append(transaction)
            logger.info(
                f"Priority transaction added to queue: id={transaction.transaction_id}"
            )
        else:
            self.transactions.append(transaction)
            logger.info(f"Transaction added to queue: id={transaction.transaction_id}")

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
    def __init__(self, bank: Bank, external_transfer_commission: float = 0.00):
        """Initialize transaction processor.

        Args:
            bank: Bank object.
            external_transfer_commission: External transfer commission rate.
        """
        self.bank = bank
        self.external_transfer_commission = external_transfer_commission
        self.queue = TransactionQueue()
        self.processed_transactions = []
        self.failed_transactions = []

        logger.info(
            f"TransactionProcessor created: external_commission={self.external_transfer_commission}"
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

    def _check_balance_allowed(self, account: BankAccount, amount: float, transaction: Transaction) -> bool:
        """Check if balance is sufficient for transaction.

        Args:
            account: Account to check.
            amount: Required amount.
            transaction: Transaction object.

        Returns:
            bool: Permission result.
        """
        if account is None:
            return True

        if isinstance(account, PremiumAccount):
            allowed_balance = account.balance + account.overdraft_limit
            if amount > allowed_balance:
                transaction.mark_failed(
                    f"Insufficient funds including overdraft: {account.account_id}"
                )
                logger.error(
                    f"Transaction blocked: insufficient funds with overdraft {account.account_id}"
                )
                return False
        else:
            if amount > account.balance:
                transaction.mark_failed(f"Insufficient funds: {account.account_id}")
                logger.error(f"Transaction blocked: insufficient funds {account.account_id}")
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
            transaction.from_account.balance -= commission
            logger.info(
                f"Commission applied: transaction={transaction.transaction_id}, amount={commission}"
            )

    def process_transaction(self, transaction: Transaction) -> bool:
        """Process single transaction.

        Args:
            transaction: Transaction object.

        Returns:
            bool: Processing result.
        """
        logger.info(f"Processing transaction: id={transaction.transaction_id}")
        transaction.transaction_status = "processing"
        transaction.updated_at = datetime.now().isoformat(timespec="seconds")

        if not self._check_account_allowed(transaction.from_account, transaction):
            self.failed_transactions.append(transaction)
            return False

        if not self._check_account_allowed(transaction.to_account, transaction):
            self.failed_transactions.append(transaction)
            return False

        required_amount = transaction.amount + self._calculate_commission(transaction)
        if not self._check_balance_allowed(transaction.from_account, required_amount, transaction):
            self.failed_transactions.append(transaction)
            return False

        try:
            if transaction.transaction_type == "deposit":
                if transaction.to_account is not None:
                    transaction.to_account.balance += transaction.amount

            elif transaction.transaction_type == "withdrawal":
                if transaction.from_account is not None:
                    transaction.from_account.balance -= transaction.amount

            elif transaction.transaction_type in ["transfer", "external_transfer"]:
                if transaction.from_account is not None:
                    transaction.from_account.balance -= transaction.amount
                if transaction.to_account is not None:
                    transaction.to_account.balance += transaction.amount

                self._apply_commission(transaction)

            else:
                transaction.mark_failed(f"Unknown transaction type: {transaction.transaction_type}")
                self.failed_transactions.append(transaction)
                return False

            transaction.mark_completed()
            self.processed_transactions.append(transaction)
            logger.info(f"Transaction processed successfully: id={transaction.transaction_id}")
            return True

        except Exception as error:
            transaction.mark_failed(str(error))
            self.failed_transactions.append(transaction)
            logger.error(f"Transaction processing error: id={transaction.transaction_id}, error={error}")
            return False

    def process_queue(self) -> dict:
        """Process all transactions in queue.

        Returns:
            dict: Processing results.
        """
        logger.info("Processing transaction queue started")

        all_transactions = self.queue.priority_transactions + self.queue.transactions
        success_count = 0
        fail_count = 0

        for transaction in all_transactions:
            if self.process_transaction(transaction):
                success_count += 1
            else:
                fail_count += 1

        self.queue.transactions = []
        self.queue.priority_transactions = []

        result = {
            "processed": success_count,
            "failed": fail_count,
            "total": len(all_transactions),
        }

        logger.info(
            f"Queue processing finished: processed={result['processed']}, failed={result['failed']}"
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
