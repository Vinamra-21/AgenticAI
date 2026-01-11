from datetime import datetime
from typing import Dict, List, NamedTuple, Optional, Callable

# --- Data Structures ---

class Transaction(NamedTuple):
    """Represents a single financial event within the account."""
    timestamp: datetime
    type: str
    symbol: Optional[str]
    quantity: Optional[int]
    price: Optional[float]
    amount: float

class ShareHolding(NamedTuple):
    """Represents the aggregated position of a specific share symbol."""
    symbol: str
    quantity: int
    total_cost_basis: float

# --- External Dependency Mock Implementation ---

def get_share_price(symbol: str) -> float:
    """
    Fetches the current market price for a given ticker symbol.
    Includes a test implementation that returns fixed prices.
    """
    prices = {
        'AAPL': 150.00,
        'TSLA': 250.00,
        'GOOGL': 100.00
    }
    if symbol in prices:
        return prices[symbol]
    raise ValueError(f"Unknown symbol: {symbol}")

# --- Main Class ---

class Account:
    """
    Manages a user's trading simulation account.
    Handles fund management, share transactions, and portfolio valuation.
    """

    def __init__(self, account_id: str, initial_deposit: float = 0.0):
        """
        Initializes a new account.
        If initial_deposit is provided, it calls deposit.
        """
        self.account_id = account_id
        self.cash_balance = 0.0
        self.initial_deposit = 0.0
        self.holdings: Dict[str, ShareHolding] = {}
        self.transactions: List[Transaction] = []

        if initial_deposit > 0:
            self.deposit(initial_deposit)

    def deposit(self, amount: float) -> None:
        """
        Adds funds to the account's cash balance.
        Updates initial_deposit and records a transaction.
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        
        self.cash_balance += amount
        self.initial_deposit += amount
        
        txn = Transaction(
            timestamp=datetime.now(),
            type='DEPOSIT',
            symbol=None,
            quantity=None,
            price=None,
            amount=amount
        )
        self.transactions.append(txn)

    def withdraw(self, amount: float) -> None:
        """
        Deducts funds from the cash balance. Records a transaction.
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if amount > self.cash_balance:
            raise ValueError("Insufficient funds to withdraw.")

        self.cash_balance -= amount
        
        txn = Transaction(
            timestamp=datetime.now(),
            type='WITHDRAWAL',
            symbol=None,
            quantity=None,
            price=None,
            amount=-amount # Stored as negative for consistency in ledger
        )
        self.transactions.append(txn)

    def buy_shares(self, symbol: str, quantity: int, price_func: Callable[[str], float]) -> None:
        """
        Records the purchase of shares.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        
        try:
            price = price_func(symbol)
        except ValueError:
            raise ValueError(f"Invalid symbol provided: {symbol}")

        total_cost = price * quantity

        if self.cash_balance < total_cost:
            raise ValueError("Insufficient funds to buy shares.")

        # Update Cash
        self.cash_balance -= total_cost

        # Update Holdings
        self._update_holding_on_buy(symbol, quantity, price)

        # Record Transaction
        txn = Transaction(
            timestamp=datetime.now(),
            type='BUY',
            symbol=symbol,
            quantity=quantity,
            price=price,
            amount=-total_cost # Negative because cash is leaving
        )
        self.transactions.append(txn)

    def sell_shares(self, symbol: str, quantity: int, price_func: Callable[[str], float]) -> None:
        """
        Records the sale of shares.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        
        if symbol not in self.holdings or self.holdings[symbol].quantity < quantity:
            raise ValueError("Insufficient shares held to sell.")

        try:
            price = price_func(symbol)
        except ValueError:
            raise ValueError(f"Invalid symbol provided: {symbol}")

        total_proceeds = price * quantity

        # Update Cash
        self.cash_balance += total_proceeds

        # Update Holdings
        self._update_holding_on_sell(symbol, quantity, price)

        # Record Transaction
        txn = Transaction(
            timestamp=datetime.now(),
            type='SELL',
            symbol=symbol,
            quantity=quantity,
            price=price,
            amount=total_proceeds # Positive because cash is entering
        )
        self.transactions.append(txn)

    def get_portfolio_value(self, price_func: Callable[[str], float]) -> float:
        """
        Calculates the total value of the account (Cash + Value of all Holdings).
        """
        market_value = 0.0
        for holding in self.holdings.values():
            try:
                current_price = price_func(holding.symbol)
                market_value += current_price * holding.quantity
            except ValueError:
                # If a symbol is unknown to price_func, we ignore its value or could log error.
                # For this simulation, we assume valid holdings have valid prices.
                pass
        return self.cash_balance + market_value

    def get_profit_loss(self, price_func: Callable[[str], float]) -> float:
        """
        Calculates the total Profit or Loss relative to the initial deposit.
        Formula: (Cash + Market Value of Shares) - Initial Deposit.
        """
        current_value = self.get_portfolio_value(price_func)
        return current_value - self.initial_deposit

    def get_holdings_report(self) -> Dict[str, int]:
        """
        Returns a simple dictionary of currently held symbols and quantities.
        """
        return {symbol: holding.quantity for symbol, holding in self.holdings.items()}

    def get_transaction_history(self) -> List[Transaction]:
        """
        Returns the list of all recorded transactions.
        """
        return self.transactions

    def _update_holding_on_buy(self, symbol: str, quantity: int, price: float) -> None:
        """Private Helper: Updates the internal holdings dictionary after a buy."""
        if symbol in self.holdings:
            current = self.holdings[symbol]
            new_qty = current.quantity + quantity
            new_cost = current.total_cost_basis + (quantity * price)
            self.holdings[symbol] = ShareHolding(symbol, new_qty, new_cost)
        else:
            self.holdings[symbol] = ShareHolding(symbol, quantity, quantity * price)

    def _update_holding_on_sell(self, symbol: str, quantity: int, price: float) -> None:
        """Private Helper: Updates the internal holdings dictionary after a sell."""
        current = self.holdings[symbol]
        if current.quantity == quantity:
            # Selling all shares of this symbol
            del self.holdings[symbol]
        else:
            # Selling partial shares
            new_qty = current.quantity - quantity
            # Proportional reduction in cost basis
            cost_reduction = current.total_cost_basis * (quantity / current.quantity)
            new_cost = current.total_cost_basis - cost_reduction
            self.holdings[symbol] = ShareHolding(symbol, new_qty, new_cost)