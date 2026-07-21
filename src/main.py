from models import BankAccount, InsufficientFundsError, AccountFrozenError


def main() -> None:
    active_account = BankAccount(None, owner="Ivan Ivanov", balance=1500, status="active", currency="RUB")
    frozen_account = BankAccount(None, owner="Anna Smirnova", balance=800, status="frozen", currency="USD")

    print("Accounts:")
    print(active_account)
    print(frozen_account)
    print()

    print("Valid operations on active account:")
    active_account.deposit(500)
    print("After deposit:", active_account)

    try:
        active_account.withdraw(3000)
    except InsufficientFundsError as error:
        print("Withdraw error:", error)

    active_account.withdraw(700)
    print("After withdraw:", active_account)
    print()

    print("Attempt operations on frozen account:")
    try:
        frozen_account.deposit(100)
    except AccountFrozenError as error:
        print("Deposit error:", error)

    try:
        frozen_account.withdraw(50)
    except AccountFrozenError as error:
        print("Withdraw error:", error)
    print()

    print("Account info dict:")
    print(active_account.get_account_info())


if __name__ == "__main__":
    main()