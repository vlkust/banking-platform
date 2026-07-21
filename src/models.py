from uuid import uuid4


class AccountFrozenError(Exception):
    pass


class AccountClosedError(Exception):
    pass


class InvalidOperationError(Exception):
    pass


class InsufficientFundsError(Exception):
    pass


class AbstractAccount:
    def __init__(self, account_id: str | None = None, owner: str = "", balance: float = 0.0, status: str = ""):
        self.account_id = account_id
        self.owner = owner
        self.balance = balance
        self.status = status

    def deposit(self, amount: float) -> None:
        pass

    def withdraw(self, amount: float) -> None:
        pass

    def get_account_info(self) -> None:
        pass


class BankAccount(AbstractAccount):
    def __init__(self, account_id: str | None = None, owner: str = "", balance: float = 0.0, status: str = "", currency: str = ""):
        self.account_id = account_id
        self.owner = owner
        self.balance = balance
        self.status = status
        self.currency = currency

        self.ALLOWED_STATUS_LIST = ["active", "frozen", "closed"]
        self.ALLOWED_CURRENCY_LIST = ["RUB", "USD", "EUR", "KZT", "CNY"]

        self.balance_validatinon()
        self.status_validatinon()
        self.currency_validatinon()

        if not self.account_id:
            self.account_id = self.generate_account_id()

    def generate_account_id(self) -> str:
        """Generate a short unique account identifier.

        Returns:
            str: Short uppercase identifier based on UUID.
        """
        return uuid4().hex[:8].upper()
    
    def balance_validatinon(self) -> None:
        """Validate the balance.

        Args:
            balance: Initial balance value.

        Raises:
            InvalidOperationError: If balance is not numeric or is negative.
        """
        if not isinstance(self.balance, (int, float)):
            raise InvalidOperationError("Balance must be a number.")
        
        if self.balance < 0:
            raise InvalidOperationError("Balance must be greater than zero.")
        
    def status_validatinon(self) -> None:
        """Validate the status.

        Args:
            status: Status to validate.

        Raises:
            InvalidOperationError: If status is not in the allowed status list.
        """
        if self.status not in self.ALLOWED_STATUS_LIST:
            raise InvalidOperationError(f"Invalid status: {self.status}.")
        
    def currency_validatinon(self) -> None:
        """Validate the account currency.

        Args:
            currency: Currency to validate.

        Raises:
            InvalidOperationError: If currency is not in the allowed currency list.
        """
        if self.currency not in self.ALLOWED_CURRENCY_LIST:
            raise InvalidOperationError(f"Invalid currency: {self.status}.")
        
    def check_account_status(self) -> None:
        """Check whether operations are allowed for the current status.

        Raises:
            AccountFrozenError: If the account is frozen.
            AccountClosedError: If the account is closed.
        """
        if self.status == "frozen":
            raise AccountFrozenError("Account is frozen.")
        if self.status == "closed":
            raise AccountClosedError("Account is closed.")
        
    def is_balance_sufficient(self, amount) -> None:
        """Check the sufficient of the balance.

        Args:
            balance: Initial balance value.
            amount: Deposit or withdrawal amount.

        Raises:
            InsufficientFundsError: If the balance is insufficient for withdrawal.
        """
        if amount > self.balance:
            raise InsufficientFundsError("Insufficient funds.")
        
    def amount_validatinon(self, amount) -> None:
        """Validate the transaction amount.

        Args:
            amount: Deposit or withdrawal amount.

        Returns:
            float: Validated amount converted to float.

        Raises:
            InvalidOperationError: If amount is not numeric or is not positive.
        """
        if not isinstance(amount, (int, float)):
            raise InvalidOperationError("Amount must be a number.")
        
        if amount <= 0:
            raise InvalidOperationError("Amount must be greater than zero.")
        
    def deposit(self, amount: float) -> None:
        """Deposit funds into the account.

        Args:
            amount: Amount to deposit.

        Raises:
            AccountFrozenError: If the account is frozen.
            AccountClosedError: If the account is closed.
            InvalidOperationError: If amount is invalid.
        """
        self.check_account_status()
        self.amount_validatinon(amount)
        self.balance += amount
    
    def withdraw(self, amount: float) -> None:
        """Withdraw funds from the account.

        Args:
            amount: Amount to withdraw.

        Raises:
            AccountFrozenError: If the account is frozen.
            AccountClosedError: If the account is closed.
            InvalidOperationError: If amount is invalid.
            InsufficientFundsError: If balance is not enough.
        """
        self.check_account_status()
        self.amount_validatinon(amount)
        self.is_balance_sufficient(amount)
        self.balance -= amount
        
    def get_account_info(self) -> dict:
        """Return structured account information.

        Returns:
            dict: Dictionary with account details.
        """
        return {
            "account_id": self.account_id,
            "owner": self.owner,
            "balance": self.balance,
            "currency": self.currency,
            "status": self.status,
            "account_type": self.__class__.__name__,
        }
    
    def __str__(self) -> str:
        """Return a readable string representation of the account.

        Returns:
            str: Readable account description.
        """
        last4 = self.account_id[-4:]
        return (
            f"{self.__class__.__name__} | "
            f"Owner: {self.owner} | "
            f"ID: ****{last4} | "
            f"Status: {self.status} | "
            f"Balance: {self.balance:.2f} {self.currency}"
        )