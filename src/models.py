from abc import ABC, abstractmethod
from uuid import uuid4
from exceptions import InvalidOperationError, AccountFrozenError, AccountClosedError, InsufficientFundsError
from utils import (
                logger, 
                numeric_value_validation, 
                string_value_validation, 
                ALLOWED_STATUS_LIST, 
                ALLOWED_CURRENCY_LIST, 
                ALLOWED_PORTFOLIO_ASSETS_LIST
                )


class AbstractAccount(ABC):
    def __init__(self, account_id: str | None = None, owner: str = "", balance: float = 0.0, status: str = ""):
        """Initialize abstract account fields.

        Args:
            account_id: Unique account identifier.
            owner: Account owner.
            balance: Initial balance.
            status: Current account status.
        """
        
        self.account_id = account_id
        self.owner = owner

        self._balance = 0.0
        self._status = ""
        
        self.status = status
        self.balance = balance

        logger.info(f"Account initialized: id={self.account_id}, owner={self.owner}, status={self.status}")

    @property
    def balance(self) -> float:
        """Return current balance value.

        Returns:
            float: Protected account balance.
        """
        return self._balance
    
    @balance.setter
    def balance(self, value: float) -> None:
        """Validate and set protected balance.

        Args:
            value: New balance value.
        """
        numeric_value_validation(value, "balance")
        self._balance = value

    @property
    def status(self) -> str:
        """Return current status value.

        Returns:
            float: Protected account status.
        """
        return self._status
    
    @status.setter
    def status(self, value: str) -> None:
        """Validate and set protected status.

        Args:
            value: New status value.
        """
        string_value_validation(value, ALLOWED_STATUS_LIST, "status")
        self._status = value

    @abstractmethod
    def deposit(self, amount: float) -> None:
        """Deposit money into the account."""
        raise NotImplementedError

    @abstractmethod
    def withdraw(self, amount: float) -> None:
        """Withdraw money from the account."""
        raise NotImplementedError

    @abstractmethod
    def get_account_info(self) -> dict:
        """Return structured account information."""
        raise NotImplementedError


class BankAccount(AbstractAccount):
    def __init__(self, account_id: str | None = None, owner: str = "", balance: float = 0.0, status: str = "", currency: str = ""):
        """Initialize a standard bank account.

        Args:
            account_id: Unique account identifier.
            owner: Account owner.
            balance: Initial balance.
            status: Account status.
            currency: Account currency.
        """
        super().__init__(account_id, owner, balance, status)
        self.currency = currency

        numeric_value_validation(self.balance, "balance")
        string_value_validation(self.status, ALLOWED_STATUS_LIST, "status")
        string_value_validation(self.currency, ALLOWED_CURRENCY_LIST, "currency")

        if not self.account_id:
            self.account_id = self._generate_account_id()
            logger.info(f"Account_id generated: {self.account_id}")

        logger.info(f"BankAccount created: id={self.account_id}, owner={self.owner}, currency={self.currency}")

    def _generate_account_id(self) -> str:
        """Generate a short unique account identifier.

        Returns:
            str: Short uppercase identifier based on UUID.
        """
        return uuid4().hex[:8].upper()
        
    def _check_account_status(self) -> None:
        """Check whether operations are allowed for the current status.

        Raises:
            AccountFrozenError: If the account is frozen.
            AccountClosedError: If the account is closed.
        """
        string_value_validation(self.status, ALLOWED_STATUS_LIST, "status")

        if self.status == "frozen":
            logger.warning(f"Operation blocked: frozen account id={self.account_id}")
            raise AccountFrozenError("Account is frozen.")
        if self.status == "closed":
            logger.warning(f"Operation blocked: closed account id={self.account_id}")
            raise AccountClosedError("Account is closed.")
        
    def _is_balance_sufficient(self, amount: float) -> None:
        """Check the sufficient of the balance.

        Args:
            balance: Initial balance value.
            amount: Deposit or withdrawal amount.

        Raises:
            InsufficientFundsError: If the balance is insufficient for withdrawal.
        """
        if amount > self.balance:
            logger.error(f"Withdrawal failed: id={self.account_id}, amount={amount}, balance={self.balance}")
            raise InsufficientFundsError("Insufficient funds.")
        
    def deposit(self, amount: float) -> None:
        """Deposit funds into the account.

        Args:
            amount: Amount to deposit.

        Raises:
            AccountFrozenError: If the account is frozen.
            AccountClosedError: If the account is closed.
            InvalidOperationError: If amount is invalid.
        """
        numeric_value_validation(amount, "amount")

        self._check_account_status()
        self.balance += amount
        logger.info(f"Deposit successful: id={self.account_id}, amount={amount}, new_balance={self.balance}")
    
    def withdraw(self, amount: float) -> None:
        """Withdraw funds from the account.

        Args:
            amount: Amount to withdraw.
        """
        numeric_value_validation(amount, "amount")

        self._check_account_status()
        self._is_balance_sufficient(amount)
        self.balance -= amount
        logger.info(f"Withdrawal successful: id={self.account_id}, amount={amount}, new_balance={self.balance}")
        
    def get_account_info(self) -> dict:
        """Return bank account information.

        Returns:
            dict: Bank account data.
        """
        return {
                "account_id": self.account_id,
                "owner": self.owner,
                "status": self.status,
                "balance": self.balance,
                "currency": self.currency,
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
    

class SavingsAccount(BankAccount):
    def __init__(self, 
                 account_id: str | None = None, 
                 owner: str = "", 
                 balance: float = 0.0, 
                 status: str = "", 
                 currency: str = "", 
                 min_balance: float = 0.0, 
                 monthly_interest_rate: float = 0.0
                 ):
        """Initialize savings account.

        Args:
            account_id: Unique account identifier.
            owner: Account owner.
            balance: Initial balance.
            status: Account status.
            currency: Account currency.
            min_balance: Minimum required balance.
            monthly_interest_rate: Monthly interest rate in percent.
        """

        super().__init__(account_id, owner, balance, status, currency)
        self.min_balance = min_balance
        self.monthly_interest_rate = monthly_interest_rate

        numeric_value_validation(self.min_balance, "min_balance")
        numeric_value_validation(self.monthly_interest_rate, "monthly_interest_rate")

        logger.info(
            f"SavingsAccount created: id={self.account_id}, min_balance={self.min_balance}, "
            f"monthly_interest_rate={self.monthly_interest_rate}"
        )

    def _is_balance_sufficient(self, amount: float) -> None:
        """Check the sufficient of the balance.

        Args:
            balance: Initial balance value.
            amount: Deposit or withdrawal amount.

        Raises:
            InsufficientFundsError: If the balance is insufficient for withdrawal.
        """
        if self.balance - amount < self.min_balance:
            logger.error(
                f"Savings withdrawal denied: id={self.account_id}, amount={amount}, "
                f"balance={self.balance}, min_balance={self.min_balance}"
            )
            raise InsufficientFundsError(
                "Cannot withdraw: minimum balance requirement would be violated."
            )


    def withdraw(self, amount: float) -> None:
        """Withdraw funds while keeping minimum balance.

        Args:
            amount: Amount to withdraw.
        """
        numeric_value_validation(self.min_balance, "min_balance")
        numeric_value_validation(amount, "amount")

        self._check_account_status()
        self._is_balance_sufficient(amount)

        self.balance -= amount
        logger.info(
            f"Savings withdrawal successful: id={self.account_id}, amount={amount}, "
            f"new_balance={self.balance}"
        )

    def apply_monthly_interest(self) -> float:
        """Apply monthly interest to account balance.

        Returns:
            float: Interest amount added to balance.
        """
        self._check_account_status()
        numeric_value_validation(self.monthly_interest_rate, "monthly_interest_rate")

        interest_amount = self.balance * (self.monthly_interest_rate / 100)
        self.balance += interest_amount

        logger.info(
            f"Monthly interest applied: id={self.account_id}, interest={interest_amount}, "
            f"new_balance={self.balance}"
        )
        return interest_amount
    
    def get_account_info(self) -> dict:
        """Return savings account information.

        Returns:
            dict: Savings account data.
        """
        info = super().get_account_info()
        info.update(
            {
                "min_balance": self.min_balance,
                "monthly_interest_rate": self.monthly_interest_rate,
            }
        )
        return info

    def __str__(self) -> str:
        """Return readable savings account description.

        Returns:
            str: String representation of savings account.
        """
        return (
            f"{super().__str__()} | "
            f"Min balance: {self.min_balance:.2f} {self.currency} | "
            f"Interest: {self.monthly_interest_rate:.2f}%"
        )


class PremiumAccount(BankAccount):
    def __init__(self, 
                 account_id: str | None = None, 
                 owner: str = "", 
                 balance: float = 0.0, 
                 status: str = "", 
                 currency: str = "", 
                 overdraft_limit: float = 0.0,
                 withdrawal_limit: float = 100000.0,
                 fixed_commission: float = 0.0
                 ):
        """Initialize premium account.

        Args:
            account_id: Unique account identifier.
            owner: Account owner.
            balance: Initial balance.
            status: Account status.
            currency: Account currency.
            overdraft_limit: Allowed overdraft amount.
            withdrawal_limit: Maximum amount per withdrawal.
            fixed_commission: Fixed commission charged on withdrawal.
        """
        
        super().__init__(account_id, owner, balance, status, currency)
        self.overdraft_limit = overdraft_limit
        self.withdrawal_limit = withdrawal_limit
        self.fixed_commission = fixed_commission

        numeric_value_validation(self.overdraft_limit, "overdraft_limit")
        numeric_value_validation(self.withdrawal_limit, "withdrawal_limit")
        numeric_value_validation(self.fixed_commission, "fixed_commission")

        logger.info(
            f"PremiumAccount created: id={self.account_id}, overdraft_limit={self.overdraft_limit}, "
            f"withdrawal_limit={self.withdrawal_limit}, fixed_commission={self.fixed_commission}"
        )

    def _check_withdraw_limits(self, amount: float) -> None:
        """Checking that withdrawal limits are sufficient.

        Args:
            withdrawal_limit: Maximum amount per withdrawal.
            amount: Deposit or withdrawal amount.

        Raises:
            InvalidOperationError: If the withdrawal limits is insufficient for withdrawal.
        """
        if amount > self.withdrawal_limit:
            logger.error(
                f"Premium withdrawal limit exceeded: id={self.account_id}, amount={amount}, "
                f"limit={self.withdrawal_limit}"
            )
            raise InvalidOperationError(
                f"Withdrawal limit exceeded. Maximum allowed: {self.withdrawal_limit}"
            )

    def _is_balance_sufficient(self, amount_with_commission: float) -> None:
        """Check the sufficient of the balance.

        Args:
            amount_with_commission: Deposit or withdrawal amount including commission.

        Raises:
            InsufficientFundsError: If the balance is insufficient for withdrawal.
        """
        allowed_balance = self.balance + self.overdraft_limit

        if amount_with_commission > allowed_balance:
            logger.error(
                f"Premium withdrawal denied: id={self.account_id}, amount_with_commission={amount_with_commission}, "
                f"balance={self.balance}, overdraft_limit={self.overdraft_limit}"
            )
            raise InsufficientFundsError(
                "Insufficient funds including overdraft limit."
            )

    def withdraw(self, amount: float) -> None:
        """Withdraw funds while keeping minimum balance.

        Args:
            amount: Amount to withdraw.
        """
        numeric_value_validation(self.overdraft_limit, "overdraft_limit")
        numeric_value_validation(self.withdrawal_limit, "withdrawal_limit")
        numeric_value_validation(self.fixed_commission, "fixed_commission")
        numeric_value_validation(amount, "amount")

        self._check_account_status()
        self._check_withdraw_limits(amount)

        amount_with_commission = amount + self.fixed_commission
        self._is_balance_sufficient(amount_with_commission)

        self.balance -= amount_with_commission
        logger.info(
            f"Premium withdrawal successful: id={self.account_id}, amount={amount}, "
            f"commission={self.fixed_commission}, new_balance={self.balance}"
        )
    
    def get_account_info(self) -> dict:
        """Return premium account information.

        Returns:
            dict: Premium account data.
        """
        info = super().get_account_info()
        info.update(
            {
                "overdraft_limit": self.overdraft_limit,
                "withdrawal_limit": self.withdrawal_limit,
                "fixed_commission": self.fixed_commission,
            }
        )
        return info

    def __str__(self) -> str:
        """Return readable premium account description.

        Returns:
            str: String representation of premium account.
        """
        return (
            f"{super().__str__()} | "
            f"Overdraft: {self.overdraft_limit:.2f} {self.currency} | "
            f"Commission: {self.fixed_commission:.2f} {self.currency}"
        )


class InvestmentAccount(BankAccount):
    def __init__(self, 
                 account_id: str | None = None, 
                 owner: str = "", 
                 balance: float = 0.0, 
                 status: str = "", 
                 currency: str = "", 
                 portfolio: dict | None = None
                 ):
        """Initialize investment account.

        Args:
            account_id: Unique account identifier.
            owner: Account owner.
            balance: Initial balance.
            status: Account status.
            currency: Account currency.
            portfolio: Asset portfolio with categories like stocks, bonds, etf.
        """

        super().__init__(account_id, owner, balance, status, currency)
        self.portfolio = portfolio if portfolio is not None else {
            "stocks": 0.0,
            "bonds": 0.0,
            "etf": 0.0,
        }
        self._check_portfolio_assets(self.portfolio)

        logger.info(f"InvestmentAccount created: id={self.account_id}, portfolio={self.portfolio}")

    def _check_portfolio_assets(self, portfolio):
        """Checking that every item in portfolio.

        Args:
            portfolio: Asset portfolio with categories like stocks, bonds, etf.
        """
        for asset_name, asset_value in portfolio.items():
            string_value_validation(asset_name, ALLOWED_PORTFOLIO_ASSETS_LIST, "portfolio." + asset_name)
            numeric_value_validation(asset_value, "portfolio." + asset_name)

    def withdraw(self, amount: float) -> None:
        """Withdraw funds from investment account.

        Args:
            amount: Amount to withdraw.

        Raises:
            InsufficientFundsError: If balance is insufficient.
        """
        numeric_value_validation(amount, "amount")

        self._check_account_status()
        self._is_balance_sufficient(amount)
        self.balance -= amount

        logger.info(
            f"Investment withdrawal successful: id={self.account_id}, amount={amount}, "
            f"new_balance={self.balance}"
        )

    def project_yearly_growth(self, growth_rates: dict) -> float:
        """Project yearly growth of the investment portfolio.

        Args:
            growth_rates: Expected annual growth rates in percent for each asset type.

        Returns:
            float: Total projected portfolio value after one year.
        """
        projected_value = 0.0

        self._check_portfolio_assets(self.portfolio)
        self._check_portfolio_assets(growth_rates)

        for asset_name, asset_value in self.portfolio.items():
            rate = growth_rates.get(asset_name, 0)
            projected_value += asset_value * (1 + rate / 100)

        logger.info(
            f"Investment projection calculated: id={self.account_id}, projected_value={projected_value}"
        )
        return projected_value
    
    def get_account_info(self) -> dict:
        """Return investment account information.

        Returns:
            dict: Investment account data.
        """
        info = super().get_account_info()
        info.update({"portfolio": self.portfolio})
        return info

    def __str__(self) -> str:
        """Return readable investment account description.

        Returns:
            str: String representation of investment account.
        """
        return f"{super().__str__()} | Portfolio: {self.portfolio}"