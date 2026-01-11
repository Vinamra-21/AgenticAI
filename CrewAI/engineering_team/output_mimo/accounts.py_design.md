```markdown
# accounts.py - Detailed Module Design

## Overview
This document provides the detailed design for the `accounts.py` module, containing the `Account` class and supporting structures to manage a user's trading simulation account. The module is designed to be self-contained, handling fund management, share transactions, and portfolio valuation.

## Data Structures

### `Transaction` (NamedTuple or Dataclass)
Represents a single financial event within the account.

*   **Attributes:**
    *   `timestamp` (datetime): The time the transaction occurred.
    *   `type` (str): Type of transaction ('DEPOSIT', 'WITHDRAWAL', 'BUY', 'SELL').
    *   `symbol` (str): Ticker symbol (None for cash transactions).
    *   `quantity` (int): Number of shares (None for cash transactions).
    *   `price` (float): Price per share at the time of transaction (None for cash transactions).
    *   `amount` (float): Total cash amount involved (positive for deposit/buy, negative for withdrawal/sell).

### `ShareHolding` (NamedTuple or Dataclass)
Represents the aggregated position of a specific share symbol.

*   **Attributes:**
    *   `symbol` (str): Ticker symbol.
    *   `quantity` (int): Total shares held.
    *   `total_cost_basis` (float): Total money spent to acquire these shares (used for P/L calculation).

## External Dependency
The module requires an external function to function. A mock implementation is provided in the design for testing purposes.

*   **Function:** `get_share_price(symbol: str) -> float`
    *   **Description:** Fetches the current market price for a given ticker symbol.
    *   **Mock Implementation:** Returns fixed values for 'AAPL' (150.00), 'TSLA' (250.00), and 'GOOGL' (100.00). Raises `ValueError` for unknown symbols.

## Class: `Account`

### Attributes
*   `account_id` (str): Unique identifier for the account.
*   `cash_balance` (float): Current liquid funds available.
*   `initial_deposit` (float): The total amount of cash deposited over the lifetime of the account.
*   `holdings` (Dict[str, ShareHolding]): A dictionary mapping symbol to `ShareHolding` objects.
*   `transactions` (List[Transaction]): A chronological list of all transactions performed.

### Methods

#### `__init__(self, account_id: str, initial_deposit: float = 0.0)`
*   **Description:** Initializes a new account. If `initial_deposit` is provided, it calls `deposit`.
*   **Parameters:**
    *   `account_id`: Unique ID for the user.
    *   `initial_deposit`: Optional starting cash amount.

#### `deposit(self, amount: float) -> None`
*   **Description:** Adds funds to the account's cash balance. Updates `initial_deposit` and records a transaction.
*   **Parameters:**
    *   `amount`: The amount of cash to deposit (must be > 0).
*   **Raises:** `ValueError` if amount is not positive.

#### `withdraw(self, amount: float) -> None`
*   **Description:** Deducts funds from the cash balance. Records a transaction.
*   **Parameters:**
    *   `amount`: The amount of cash to withdraw (must be > 0).
*   **Raises:** `ValueError` if amount is not positive or if `amount` > `cash_balance`.

#### `buy_shares(self, symbol: str, quantity: int, price_func: callable) -> None`
*   **Description:** Records the purchase of shares.
    *   1. Validates symbol via `price_func`.
    *   2. Calculates total cost (price * quantity).
    *   3. Checks if `cash_balance` >= total cost.
    *   4. Deducts cash.
    *   5. Updates `holdings` (creates new entry or updates existing `ShareHolding` with new cost basis).
    *   6. Records transaction.
*   **Parameters:**
    *   `symbol`: Ticker symbol to buy.
    *   `quantity`: Number of shares (must be > 0).
    *   `price_func`: Function to get current share price.
*   **Raises:** `ValueError` if quantity <= 0, insufficient funds, or invalid symbol.

#### `sell_shares(self, symbol: str, quantity: int, price_func: callable) -> None`
*   **Description:** Records the sale of shares.
    *   1. Validates symbol and checks if user holds sufficient quantity.
    *   2. Gets current price.
    *   3. Calculates total proceeds.
    *   4. Adds proceeds to `cash_balance`.
    *   5. Updates `holdings` (reduces quantity and cost basis proportionally).
    *   6. Records transaction.
*   **Parameters:**
    *   `symbol`: Ticker symbol to sell.
    *   `quantity`: Number of shares (must be > 0).
    *   `price_func`: Function to get current share price.
*   **Raises:** `ValueError` if quantity <= 0, insufficient shares held, or invalid symbol.

#### `get_portfolio_value(self, price_func: callable) -> float`
*   **Description:** Calculates the total value of the account (Cash + Value of all Holdings).
*   **Parameters:**
    *   `price_func`: Function to get current share prices.
*   **Returns:** Total portfolio value (float).

#### `get_profit_loss(self, price_func: callable) -> float`
*   **Description:** Calculates the total Profit or Loss relative to the initial deposit.
    *   Formula: `(Cash + Market Value of Shares) - Initial Deposit`.
*   **Parameters:**
    *   `price_func`: Function to get current share prices.
*   **Returns:** Net Profit/Loss (float).

#### `get_holdings_report(self) -> Dict[str, int]`
*   **Description:** Returns a simple dictionary of currently held symbols and quantities.
*   **Returns:** Dictionary mapping symbol to quantity.

#### `get_transaction_history(self) -> List[Transaction]`
*   **Description:** Returns the list of all recorded transactions.
*   **Returns:** List of `Transaction` objects.

#### `_update_holding_on_buy(self, symbol: str, quantity: int, price: float) -> None`
*   **Private Helper:** Updates the internal `holdings` dictionary after a buy.

#### `_update_holding_on_sell(self, symbol: str, quantity: int, price: float) -> None`
*   **Private Helper:** Updates the internal `holdings` dictionary after a sell.
```