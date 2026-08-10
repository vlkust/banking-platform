from pathlib import Path

from audit_models import AuditLog, RiskAnalyzer
from bank_models import Bank, Client
from report_models import ReportBuilder
from transaction_models import Transaction, TransactionProcessor
from utils import logger


def create_demo_clients(bank: Bank) -> list[Client]:
    """Create and add demo clients to the bank.

    Args:
        bank: Bank object.

    Returns:
        list[Client]: Created clients.
    """
    clients_data = [
        (
            "C001",
            "Ivan Ivanov",
            30,
            "+79990000001",
            "ivan@example.com",
        ),
        (
            "C002",
            "Anna Petrova",
            27,
            "+79990000002",
            "anna@example.com",
        ),
        (
            "C003",
            "Petr Sidorov",
            42,
            "+79990000003",
            "petr@example.com",
        ),
        (
            "C004",
            "Maria Smirnova",
            35,
            "+79990000004",
            "maria@example.com",
        ),
        (
            "C005",
            "Alex Volkov",
            24,
            "+79990000005",
            "alex@example.com",
        ),
    ]

    clients = []

    for client_id, full_name, age, phone, email in clients_data:
        client = Client(
            client_id=client_id,
            full_name=full_name,
            age=age,
            contacts={
                "phone": phone,
                "email": email,
            },
            status="active",
        )

        bank.add_client(client)
        clients.append(client)

    logger.info(
        f"Demo clients created: count={len(clients)}"
    )

    return clients


def create_demo_accounts(bank: Bank) -> list:
    """Create two accounts for each demo client.

    Args:
        bank: Bank object.

    Returns:
        list: Created accounts.
    """
    account_parameters = [
        (
            "C001",
            "Ivan Ivanov",
            5000,
            8000,
            1000,
            2.5,
        ),
        (
            "C002",
            "Anna Petrova",
            7000,
            9000,
            1500,
            3.0,
        ),
        (
            "C003",
            "Petr Sidorov",
            6000,
            10000,
            2000,
            2.0,
        ),
        (
            "C004",
            "Maria Smirnova",
            7500,
            11000,
            2000,
            2.2,
        ),
        (
            "C005",
            "Alex Volkov",
            6500,
            12000,
            2500,
            2.8,
        ),
    ]

    accounts = []

    for (
        client_id,
        owner,
        bank_balance,
        savings_balance,
        min_balance,
        interest_rate,
    ) in account_parameters:
        bank_account = bank.open_account(
            client_id,
            "BankAccount",
            owner=owner,
            balance=bank_balance,
            status="active",
            currency="RUB",
        )

        savings_account = bank.open_account(
            client_id,
            "SavingsAccount",
            owner=owner,
            balance=savings_balance,
            status="active",
            currency="RUB",
            min_balance=min_balance,
            monthly_interest_rate=interest_rate,
        )

        accounts.extend(
            [
                bank_account,
                savings_account,
            ]
        )

    logger.info(
        f"Demo accounts created: count={len(accounts)}"
    )

    return accounts


def create_normal_transactions(accounts: list) -> list[Transaction]:
    """Create normal and erroneous transactions.

    Args:
        accounts: Bank account objects.

    Returns:
        list[Transaction]: Created transactions.
    """
    transactions = []

    client_ids = [
        "C001",
        "C002",
        "C003",
        "C004",
        "C005",
    ]

    for index in range(30):
        account_index = index % len(accounts)
        client_id = client_ids[account_index // 2]

        transaction = Transaction(
            transaction_type="deposit",
            amount=100 + index * 10,
            currency="RUB",
            to_account=accounts[account_index],
            client_id=client_id,
        )

        transactions.append(transaction)

    # These transactions should fail during processing
    # because the source account does not have enough money.
    transactions.extend(
        [
            Transaction(
                transaction_type="withdrawal",
                amount=6000,
                currency="RUB",
                from_account=accounts[0],
                client_id="C001",
            ),
            Transaction(
                transaction_type="withdrawal",
                amount=7000,
                currency="RUB",
                from_account=accounts[2],
                client_id="C002",
            ),
        ]
    )

    return transactions


def create_suspicious_transactions(
    accounts: list,
) -> list[Transaction]:
    """Create suspicious transactions.

    Args:
        accounts: Bank account objects.

    Returns:
        list[Transaction]: Suspicious transactions.
    """
    transactions = [
        Transaction(
            transaction_type="transfer",
            amount=12000,
            currency="RUB",
            from_account=accounts[0],
            to_account=accounts[2],
            client_id="C001",
        ),
        Transaction(
            transaction_type="external_transfer",
            amount=11000,
            currency="RUB",
            from_account=accounts[0],
            to_account=accounts[4],
            client_id="C001",
        ),
        Transaction(
            transaction_type="transfer",
            amount=9000,
            currency="RUB",
            from_account=accounts[2],
            to_account=accounts[4],
            client_id="C002",
        ),
        Transaction(
            transaction_type="external_transfer",
            amount=13000,
            currency="RUB",
            from_account=accounts[2],
            to_account=accounts[6],
            client_id="C002",
        ),
        Transaction(
            transaction_type="transfer",
            amount=10000,
            currency="RUB",
            from_account=accounts[4],
            to_account=accounts[6],
            client_id="C003",
        ),
        Transaction(
            transaction_type="external_transfer",
            amount=14000,
            currency="RUB",
            from_account=accounts[4],
            to_account=accounts[8],
            client_id="C003",
        ),
        Transaction(
            transaction_type="transfer",
            amount=9500,
            currency="RUB",
            from_account=accounts[6],
            to_account=accounts[8],
            client_id="C004",
        ),
        Transaction(
            transaction_type="external_transfer",
            amount=15000,
            currency="RUB",
            from_account=accounts[6],
            to_account=accounts[0],
            client_id="C004",
        ),
        Transaction(
            transaction_type="transfer",
            amount=8500,
            currency="RUB",
            from_account=accounts[8],
            to_account=accounts[0],
            client_id="C005",
        ),
        Transaction(
            transaction_type="external_transfer",
            amount=16000,
            currency="RUB",
            from_account=accounts[8],
            to_account=accounts[2],
            client_id="C005",
        ),
    ]

    night_transaction = Transaction(
        transaction_type="transfer",
        amount=700,
        currency="RUB",
        from_account=accounts[0],
        to_account=accounts[2],
        client_id="C001",
    )

    night_transaction.created_at = "2026-08-09T02:30:00"
    night_transaction.updated_at = night_transaction.created_at

    transactions.append(night_transaction)

    return transactions


def analyze_and_queue_transactions(
    transactions: list[Transaction],
    processor: TransactionProcessor,
    risk_analyzer: RiskAnalyzer,
) -> tuple[list[Transaction], list[Transaction]]:
    """Analyze transactions and add allowed ones to the queue.

    Args:
        transactions: Transactions to analyze.
        processor: Transaction processor.
        risk_analyzer: Risk analyzer.

    Returns:
        tuple: Allowed and blocked transactions.
    """
    allowed_transactions = []
    blocked_transactions = []

    for index, transaction in enumerate(transactions):
        risk_result = risk_analyzer.analyze_transaction(
            transaction
        )

        logger.info(
            f"Risk result: "
            f"transaction_id={transaction.transaction_id}, "
            f"risk_level={risk_result['risk_level']}, "
            f"reasons={risk_result['reasons']}"
        )

        if risk_analyzer.block_dangerous_transaction(
            transaction,
            risk_result,
        ):
            blocked_transactions.append(transaction)

            logger.warning(
                f"Transaction rejected before queue: "
                f"id={transaction.transaction_id}"
            )
            continue

        priority = index < 3

        processor.queue.add_transaction(
            transaction=transaction,
            priority=priority,
        )

        allowed_transactions.append(transaction)

        logger.info(
            f"Transaction added to processing queue: "
            f"id={transaction.transaction_id}, "
            f"priority={priority}"
        )

    return allowed_transactions, blocked_transactions


def show_client_accounts(
    bank: Bank,
    clients: list[Client],
) -> None:
    """Show all accounts of all clients.

    Args:
        bank: Bank object.
        clients: Bank clients.
    """
    logger.info("=== Client accounts report ===")

    for client in clients:
        logger.info(
            f"Client: {client.full_name}, "
            f"client_id={client.client_id}, "
            f"accounts_count={len(client.account_ids)}"
        )

        for account_id in client.account_ids:
            account = bank.bank_accounts.get(account_id)

            if account is not None:
                logger.info(f"Account: {account}")


def show_transaction_history(
    transactions: list[Transaction],
    client_id: str,
) -> None:
    """Show transaction history for one client.

    Args:
        transactions: All project transactions.
        client_id: Client identifier.
    """
    logger.info(
        f"=== Transaction history: client_id={client_id} ==="
    )

    client_transactions = [
        transaction
        for transaction in transactions
        if transaction.client_id == client_id
    ]

    for transaction in client_transactions:
        logger.info(
            f"Transaction history item: "
            f"{transaction.get_transaction_info()}"
        )


def show_suspicious_operations(
    audit_log: AuditLog,
) -> None:
    """Show suspicious operations from audit log.

    Args:
        audit_log: Audit log object.
    """
    logger.info("=== Suspicious operations report ===")

    suspicious_records = [
        record
        for record in audit_log.records
        if (
            record["event"] == "risk_analysis"
            and record["level"] in ["WARNING", "CRITICAL"]
        )
    ]

    for record in suspicious_records:
        logger.warning(
            f"Suspicious operation: {record}"
        )


def show_final_reports(
    bank: Bank,
    processor: TransactionProcessor,
    audit_log: AuditLog,
    report_builder: ReportBuilder,
    transactions: list[Transaction],
    allowed_transactions: list[Transaction],
    blocked_transactions: list[Transaction],
) -> None:
    """Build, export and log all final reports.

    Args:
        bank: Bank object.
        processor: Transaction processor.
        audit_log: Audit log object.
        report_builder: ReportBuilder object.
        transactions: All project transactions.
        allowed_transactions: Transactions added to queue.
        blocked_transactions: Transactions blocked by risk analyzer.
    """
    logger.info("=== Final reports started ===")

    client_report = report_builder.build_client_report(
        "C001"
    )
    bank_report = report_builder.build_bank_report()
    risk_report = report_builder.build_risk_report()
    text_report = report_builder.build_text_report()

    logger.info(
        f"Client report for C001: {client_report}"
    )

    logger.info(
        f"Bank report: {bank_report}"
    )

    logger.info(
        f"Risk report: {risk_report}"
    )

    logger.info(
        f"Text report:\n{text_report}"
    )

    top_clients = bank_report["top_clients"]

    logger.info("Top 3 clients:")

    for position, client in enumerate(
        top_clients,
        start=1,
    ):
        logger.info(
            f"{position}. {client}"
        )

    logger.info(
        f"Transaction statistics: "
        f"created={len(transactions)}, "
        f"queued={len(allowed_transactions)}, "
        f"processed={len(processor.processed_transactions)}, "
        f"failed={len(processor.failed_transactions)}, "
        f"blocked={len(blocked_transactions)}"
    )

    logger.info(
        f"Total bank balance: "
        f"{bank.get_total_balance():.2f} RUB"
    )

    reports_directory = Path("reports")
    reports_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_builder.export_to_json(
        client_report,
        "reports/client_C001_report.json",
    )

    report_builder.export_to_json(
        bank_report,
        "reports/bank_report.json",
    )

    report_builder.export_to_json(
        risk_report,
        "reports/risk_report.json",
    )

    report_builder.export_to_csv(
        top_clients,
        "reports/top_clients.csv",
    )

    transaction_rows = [
        transaction.get_transaction_info()
        for transaction in transactions
    ]

    report_builder.export_to_csv(
        transaction_rows,
        "reports/transactions.csv",
    )

    report_builder.save_charts(
        "reports/charts"
    )

    logger.info(
        f"Audit error statistics: "
        f"{audit_log.get_error_statistics()}"
    )

    logger.info("=== Final reports finished ===")


def run_demo() -> None:
    """Run the complete banking platform demonstration."""
    logger.info("=== Complete demo started ===")

    bank = Bank()

    clients = create_demo_clients(bank)
    accounts = create_demo_accounts(bank)

    audit_log = AuditLog("audit_final.log")

    risk_analyzer = RiskAnalyzer(
        bank=bank,
        audit_log=audit_log,
        large_amount_limit=10000,
        frequent_operation_limit=3,
    )

    processor = TransactionProcessor(
        bank=bank,
        external_transfer_commission=0.01,
    )

    normal_transactions = create_normal_transactions(
        accounts
    )

    suspicious_transactions = create_suspicious_transactions(
        accounts
    )

    transactions = (
        normal_transactions + suspicious_transactions
    )

    logger.info(
        f"All transactions created: count={len(transactions)}"
    )

    allowed_transactions, blocked_transactions = (
        analyze_and_queue_transactions(
            transactions=transactions,
            processor=processor,
            risk_analyzer=risk_analyzer,
        )
    )

    logger.info(
        f"Queue before processing: "
        f"{processor.queue.get_queue_info()}"
    )

    processing_result = processor.process_queue()

    logger.info(
        f"Queue processing result: {processing_result}"
    )

    show_client_accounts(
        bank=bank,
        clients=clients,
    )

    show_transaction_history(
        transactions=transactions,
        client_id="C001",
    )

    show_suspicious_operations(
        audit_log=audit_log,
    )

    report_builder = ReportBuilder(
        bank=bank,
        transactions=transactions,
        audit_log=audit_log,
        processor=processor,
    )

    show_final_reports(
        bank=bank,
        processor=processor,
        audit_log=audit_log,
        report_builder=report_builder,
        transactions=transactions,
        allowed_transactions=allowed_transactions,
        blocked_transactions=blocked_transactions,
    )

    logger.info("=== Complete demo finished ===")


def main() -> None:
    """Run the complete banking platform."""
    logger.info("=== Banking platform demo started ===")

    run_demo()

    logger.info("=== Banking platform demo finished ===")


if __name__ == "__main__":
    main()