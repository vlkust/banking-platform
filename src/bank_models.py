from datetime import datetime
from account_models import (
                            BankAccount,
                            SavingsAccount,
                            PremiumAccount,
                            InvestmentAccount,
                            )
from exceptions import InvalidOperationError
from utils import logger, numeric_value_validation, string_value_validation, ALLOWED_CLIENT_STATUS_LIST, ALLOWED_ACCOUNT_ATTRIBUTES


class Client:
    def __init__(
                self,
                client_id: str,
                full_name: str,
                age: int,
                contacts: dict | None = None,
                status: str = "active",
                ):
        """Initialize client data.

        Args:
            client_id: Unique client identifier.
            full_name: Client full name.
            age: Client age.
            contacts: Contact information.
            status: Client status.

        Raises:
            InvalidOperationError: If client data is invalid.
        """
        self.client_id = client_id
        self.full_name = full_name
        self.age = age
        self.contacts = contacts if contacts is not None else {}
        self.status = status
        self.account_ids = []
        self.failed_auth_attempts = 0
        self.suspicious_actions = []

        self._client_validation()

        logger.info(f"Client created: client_id={self.client_id}, full_name={self.full_name}, status={self.status}")

    def _client_validation(self) -> None:
        """Validate client data."""
        if not isinstance(self.full_name, str):
            logger.error(f"Invalid full_name: {self.full_name}")
            raise InvalidOperationError("full_name must be a non-empty string.")

        numeric_value_validation(self.age, "age")

        if self.age < 18:
            logger.error(f"Client age restriction failed: client_id={self.client_id}, age={self.age}")
            raise InvalidOperationError("Client age must be greater than or equal to 18.")

        string_value_validation(self.status, ALLOWED_CLIENT_STATUS_LIST, "client_status")

        if not isinstance(self.contacts, dict):
            logger.error(f"Invalid contacts type: {type(self.contacts).__name__}")
            raise InvalidOperationError("contacts must be a dictionary.")

        if not isinstance(self.contacts, dict):
                    logger.error(f"Invalid contacts type: {type(self.contacts).__name__}")
                    raise InvalidOperationError("contacts must be a dictionary.")

    def add_account(self, account_id: str) -> None:
        """Add account id to client profile.

        Args:
            account_id: Account identifier.
        """
        if account_id not in self.account_ids:
            self.account_ids.append(account_id)
            logger.info(f"Client account linked: client_id={self.client_id}, account_id={account_id}")

    def get_client_info(self) -> dict:
        """Return structured client information.

        Returns:
            dict: Client data.
        """
        return {
            "client_id": self.client_id,
            "full_name": self.full_name,
            "age": self.age,
            "status": self.status,
            "contacts": self.contacts,
            "account_ids": self.account_ids,
            "failed_auth_attempts": self.failed_auth_attempts,
            "suspicious_actions": self.suspicious_actions,
        }

    def __str__(self) -> str:
        """Return readable client description.

        Returns:
            str: String representation of client.
        """
        return (
            f"Client | ID: {self.client_id} | Name: {self.full_name} | "
            f"Status: {self.status} | Accounts: {len(self.account_ids)}"
        )


class Bank:
    ACCOUNT_CLASSES = {
        "BankAccount": BankAccount,
        "SavingsAccount": SavingsAccount,
        "PremiumAccount": PremiumAccount,
        "InvestmentAccount": InvestmentAccount,
    }

    def __init__(self):
        """Initialize bank.
        """
        self.bank_clients = {}
        self.bank_accounts = {}

        logger.info(f"Bank created.")

    def _check_operation_time(self) -> None:
        """Block operations between 00:00 and 05:00.

        Raises:
            InvalidOperationError: If operation is attempted during restricted time.
        """
        current_hour = datetime.now().hour

        if 0 <= current_hour < 5:
            logger.warning(f"Operation blocked by time policy: hour={current_hour}")
            raise InvalidOperationError("Operations are not allowed from 00:00 to 05:00.")

    def _mark_suspicious_action(self, client_id: str, action: str) -> None:
        """Mark suspicious action for client.

        Args:
            client_id: Client identifier.
            action: Suspicious action description.
        """
        client = self.bank_clients.get(client_id)
        if client is None:
            return

        suspicious_record = {
            "client_id": client_id,
            "action": action,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

        client.suspicious_actions.append(suspicious_record)

        logger.warning(f"Suspicious action detected: client_id={client_id}, action={action}")

    def add_client(self, client: Client) -> None:
        """Add client to bank.

        Args:
            client: Client object.

        Raises:
            InvalidOperationError: If client already exists.
        """
        if client.client_id in self.bank_clients:
            logger.error(f"Duplicate client add attempt: client_id={client.client_id}")
            raise InvalidOperationError("Client already exists.")

        self.bank_clients[client.client_id] = client
        logger.info(f"Client added to bank: client_id={client.client_id}")

    def _bank_client_validation(self, client: Client, client_id: str) -> None:
        if client is None:
            logger.error(f"Operation failed: unknown client_id={client_id}")
            raise InvalidOperationError("Client not found.")

        if client.status == "blocked":
            logger.error(f"Operation failed: blocked client_id={client_id}")
            raise InvalidOperationError("Client is blocked.")

    def authenticate_client(self, client_id: str, provided_client_id: str) -> bool:
        """Authenticate client by id.

        Args:
            client_id: Client identifier in the bank system.
            provided_client_id: Provided credential.

        Returns:
            bool: Authentication result.

        Raises:
            InvalidOperationError: If client is blocked or not found.
        """
        client = self.bank_clients.get(client_id)
        self._bank_client_validation(client, client_id)

        if provided_client_id == client.client_id:
            client.failed_auth_attempts = 0
            logger.info(f"Authentication successful: client_id={client_id}")
            return True

        client.failed_auth_attempts += 1
        logger.warning(f"Authentication failed: client_id={client_id}, attempts={client.failed_auth_attempts}")

        if client.failed_auth_attempts >= 3:
            client.status = "blocked"
            self._mark_suspicious_action(client_id, "3 invalid authentication attempts")
            logger.error(f"Client blocked after failed authentication: client_id={client_id}")

        return False

    def open_account(self, client_id: str, account_type: str, **account_data) -> None:
        """Open account for client.

        Args:
            client_id: Client identifier.
            account_type: Account class name.
            **account_data: Parameters for account constructor.

        Returns:
            AbstractAccount: Created account.

        Raises:
            InvalidOperationError: If client or account type is invalid.
        """
        self._check_operation_time()

        client = self.bank_clients.get(client_id)
        self._bank_client_validation(client, client_id)

        account_class = self.ACCOUNT_CLASSES.get(account_type)
        if account_class is None:
            logger.error(f"Invalid account type requested: {account_type}")
            raise InvalidOperationError(f"Invalid account type: {account_type}")

        account = account_class(**account_data)
        self.bank_accounts[account.account_id] = account
        client.add_account(account.account_id)

        logger.info(f"Account opened: client_id={client_id}, account_id={account.account_id}, account_type={account_type}")
        return account

    def close_account(self, account_id: str) -> None:
        """Close account.

        Args:
            account_id: Account identifier.

        Raises:
            InvalidOperationError: If account not found.
        """
        self._check_operation_time()

        account = self.bank_accounts.get(account_id)
        if account is None:
            logger.error(f"Close account failed: unknown account_id={account_id}")
            raise InvalidOperationError("Account not found.")

        account.status = "closed"
        logger.info(f"Account closed: account_id={account_id}")


    def freeze_account(self, account_id: str) -> None:
        """Freeze account.

        Args:
            account_id: Account identifier.

        Raises:
            InvalidOperationError: If account not found.
        """
        self._check_operation_time()

        account = self.bank_accounts.get(account_id)
        if account is None:
            logger.error(f"Freeze account failed: unknown account_id={account_id}")
            raise InvalidOperationError("Account not found.")

        account.status = "frozen"
        logger.info(f"Account frozen: account_id={account_id}")

    def unfreeze_account(self, account_id: str) -> None:
        """Unfreeze account.

        Args:
            account_id: Account identifier.

        Raises:
            InvalidOperationError: If account not found.
        """
        self._check_operation_time()

        account = self.bank_accounts.get(account_id)
        if account is None:
            logger.error(f"Unfreeze account failed: unknown account_id={account_id}")
            raise InvalidOperationError("Account not found.")

        account.status = "active"
        logger.info(f"Account unfrozen: account_id={account_id}")

    def search_accounts(self, **search_criteria) -> list:
        """Search accounts by criteria.

        Args:
            **search_criteria: Parameters for account search.

        Returns:
            list: Matching account objects.
        """
        for attribute_name in search_criteria:
            string_value_validation(attribute_name, ALLOWED_ACCOUNT_ATTRIBUTES, "attribute_name")

        search_result = []

        for account in self.bank_accounts.values():
            if all(getattr(account, attr, None) == value for attr, value in search_criteria.items()):
                search_result.append(account)

        logger.info(f"Accounts search completed: criteria={search_criteria}, count={len(search_result)}")
        return search_result

    def get_total_balance(self):
        """Calculate total bank balance.

        Returns:
            float: Total balance across all accounts.
        """
        total_balance = sum(account.balance for account in self.bank_accounts.values())
        logger.info(f"Total bank balance calculated: total_balance={total_balance}")
        return total_balance

    def get_clients_ranking(self) -> list:
        """Rank clients by total balance on all their accounts.

        Returns:
            list: Sorted list of client summaries.
        """
        ranking = []

        for client in self.bank_clients.values():
            client_total = 0.0
            for account_id in client.account_ids:
                account = self.bank_accounts.get(account_id)
                if account is not None:
                    client_total += account.balance

            ranking.append(
                {
                    "client_id": client.client_id,
                    "full_name": client.full_name,
                    "total_balance": client_total,
                    "accounts_count": len(client.account_ids)
                }
            )

        ranking.sort(key=lambda item: item["total_balance"], reverse=True)

        logger.info("Clients ranking calculated")
        return ranking
