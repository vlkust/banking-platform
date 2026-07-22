from exceptions import InvalidOperationError, AccountFrozenError, AccountClosedError, InsufficientFundsError
from models import BankAccount, SavingsAccount, PremiumAccount, InvestmentAccount
from utils import logger


def run_bank_account_demo() -> None:
    """Run Day 1 demo сценарий for the base bank account."""
    logger.info("=== Day 1 demo started ===")

    active_account = BankAccount(
        None,
        owner="Ivan Ivanov",
        balance=1500,
        status="active",
        currency="RUB",
    )
    frozen_account = BankAccount(
        None,
        owner="Petr Petrov",
        balance=800,
        status="frozen",
        currency="USD",
    )

    logger.info("Created Day 1 accounts")
    logger.info(active_account)
    logger.info(frozen_account)

    logger.info("Valid operations on active account started")
    active_account.deposit(500)
    logger.info(f"After deposit: {active_account}")

    try:
        active_account.withdraw(3000)
    except InsufficientFundsError as error:
        logger.error(f"Withdraw error: {error}")

    active_account.withdraw(700)
    logger.info(f"After withdraw: {active_account}")

    logger.info("Attempt operations on frozen account started")
    try:
        frozen_account.deposit(100)
    except AccountFrozenError as error:
        logger.error(f"Deposit error: {error}")

    try:
        frozen_account.withdraw(50)
    except AccountFrozenError as error:
        logger.error(f"Withdraw error: {error}")

    logger.info(f"Account info dict: {active_account.get_account_info()}")
    logger.info("=== Day 1 demo finished ===")


def run_savings_account_demo() -> None:
    """Run Day 2 demo for SavingsAccount."""
    logger.info("=== Day 2 SavingsAccount demo started ===")

    savings_account = SavingsAccount(
        None,
        owner="Petr Petrov",
        balance=10000,
        status="active",
        currency="EUR",
        min_balance=2000,
        monthly_interest_rate=3.5,
    )

    logger.info(f"Created savings account: {savings_account}")

    savings_account.deposit(1000)
    logger.info(f"After deposit: {savings_account}")

    interest_amount = savings_account.apply_monthly_interest()
    logger.info(f"Applied monthly interest: {interest_amount}")
    logger.info(f"After interest: {savings_account}")

    try:
        savings_account.withdraw(9500)
    except InsufficientFundsError as error:
        logger.error(f"Savings withdraw error: {error}")

    savings_account.withdraw(3000)
    logger.info(f"After valid withdraw: {savings_account}")
    logger.info(f"Savings account info: {savings_account.get_account_info()}")

    logger.info("=== Day 2 SavingsAccount demo finished ===")


def run_premium_account_demo() -> None:
    """Run Day 2 demo for PremiumAccount."""
    logger.info("=== Day 2 PremiumAccount demo started ===")

    premium_account = PremiumAccount(
        None,
        owner="Ivan Ivanov",
        balance=5000,
        status="active",
        currency="USD",
        overdraft_limit=2000,
        withdrawal_limit=4000,
        fixed_commission=100,
    )

    logger.info(f"Created premium account: {premium_account}")

    premium_account.deposit(500)
    logger.info(f"After deposit: {premium_account}")

    premium_account.withdraw(3500)
    logger.info(f"After valid withdraw with commission: {premium_account}")

    try:
        premium_account.withdraw(4500)
    except InvalidOperationError as error:
        logger.error(f"Premium limit error: {error}")

    try:
        premium_account.withdraw(3900)
    except InsufficientFundsError as error:
        logger.error(f"Premium overdraft error: {error}")

    logger.info(f"Premium account info: {premium_account.get_account_info()}")
    logger.info("=== Day 2 PremiumAccount demo finished ===")


def run_investment_account_demo() -> None:
    """Run Day 2 demo for InvestmentAccount."""
    logger.info("=== Day 2 InvestmentAccount demo started ===")

    investment_account = InvestmentAccount(
        None,
        owner="Ivan Ivanov",
        balance=15000,
        status="active",
        currency="CNY",
        portfolio={
            "stocks": 7000,
            "bonds": 3000,
            "etf": 5000,
        },
    )

    logger.info(f"Created investment account: {investment_account}")

    investment_account.deposit(2000)
    logger.info(f"After deposit: {investment_account}")

    projected_value = investment_account.project_yearly_growth(
        {
            "stocks": 12,
            "bonds": 5,
            "etf": 8,
        }
    )
    logger.info(f"Projected yearly portfolio value: {projected_value}")

    investment_account.withdraw(4000)
    logger.info(f"After withdraw: {investment_account}")
    logger.info(f"Investment account info: {investment_account.get_account_info()}")

    logger.info("=== Day 2 InvestmentAccount demo finished ===")


def run_polymorphism_demo() -> None:
    """Run Day 2 polymorphism demo for all advanced account types."""
    logger.info("=== Day 2 polymorphism demo started ===")

    accounts = [
        SavingsAccount(
            None,
            owner="Ivan Ivanov",
            balance=8000,
            status="active",
            currency="RUB",
            min_balance=1500,
            monthly_interest_rate=2.0,
        ),
        PremiumAccount(
            None,
            owner="Petr Petrov",
            balance=4000,
            status="active",
            currency="USD",
            overdraft_limit=1000,
            withdrawal_limit=3000,
            fixed_commission=50,
        ),
        InvestmentAccount(
            None,
            owner="Ivan Petrov",
            balance=12000,
            status="active",
            currency="EUR",
            portfolio={
                "stocks": 6000,
                "bonds": 2000,
                "etf": 4000,
            },
        ),
    ]

    for account in accounts:
        logger.info(f"Polymorphic account object: {account}")
        logger.info(f"Polymorphic account info: {account.get_account_info()}")

    logger.info("=== Day 2 polymorphism demo finished ===")


def main() -> None:
    """Run all available project demos."""
    logger.info("=== Banking platform demo started ===")

    run_bank_account_demo()
    run_savings_account_demo()
    run_premium_account_demo()
    run_investment_account_demo()
    run_polymorphism_demo()

    logger.info("=== Banking platform demo finished ===")


if __name__ == "__main__":
    main()