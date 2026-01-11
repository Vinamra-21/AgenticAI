import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from accounts import Account, Transaction, ShareHolding, get_share_price

class TestAccount(unittest.TestCase):
    """Unit tests for the Account class and related functionality."""

    def setUp(self):
        """Set up a fresh account for each test."""
        self.account = Account(account_id="test_user_001")

    def test_initialization_no_deposit(self):
        """Test account creation without initial deposit."""
        self.assertEqual(self.account.account_id, "test_user_001")
        self.assertEqual(self.account.cash_balance, 0.0)
        self.assertEqual(self.account.initial_deposit, 0.0)
        self.assertEqual(len(self.account.transactions), 0)

    def test_initialization_with_deposit(self):
        """Test account creation with initial deposit."""
        acc = Account(account_id="test_user_002", initial_deposit=1000.0)
        self.assertEqual(acc.cash_balance, 1000.0)
        self.assertEqual(acc.initial_deposit, 1000.0)
        self.assertEqual(len(acc.transactions), 1)
        self.assertEqual(acc.transactions[0].type, 'DEPOSIT')

    def test_deposit_positive_amount(self):
        """Test depositing a valid positive amount."""
        initial_balance = self.account.cash_balance
        amount = 500.0
        self.account.deposit(amount)
        
        self.assertEqual(self.account.cash_balance, initial_balance + amount)
        self.assertEqual(self.account.initial_deposit, amount)
        self.assertEqual(len(self.account.transactions), 1)
        
        txn = self.account.transactions[0]
        self.assertEqual(txn.type, 'DEPOSIT')
        self.assertEqual(txn.amount, amount)
        self.assertIsNone(txn.symbol)

    def test_deposit_negative_amount_raises_error(self):
        """Test that depositing a negative amount raises ValueError."""
        with self.assertRaisesRegex(ValueError, "Deposit amount must be positive."):
            self.account.deposit(-100.0)

    def test_deposit_zero_amount_raises_error(self):
        """Test that depositing zero raises ValueError."""
        with self.assertRaisesRegex(ValueError, "Deposit amount must be positive."):
            self.account.deposit(0.0)

    def test_withdraw_valid_amount(self):
        """Test withdrawing a valid amount."""
        self.account.deposit(1000.0)
        withdraw_amount = 300.0
        
        self.account.withdraw(withdraw_amount)
        
        self.assertEqual(self.account.cash_balance, 700.0)
        self.assertEqual(len(self.account.transactions), 2) # Deposit + Withdrawal
        
        txn = self.account.transactions[1]
        self.assertEqual(txn.type, 'WITHDRAWAL')
        self.assertEqual(txn.amount, -withdraw_amount)

    def test_withdraw_insufficient_funds(self):
        """Test withdrawing more than available balance."""
        self.account.deposit(100.0)
        
        with self.assertRaisesRegex(ValueError, "Insufficient funds to withdraw."):
            self.account.withdraw(200.0)

    def test_withdraw_negative_amount_raises_error(self):
        """Test that withdrawing a negative amount raises ValueError."""
        with self.assertRaisesRegex(ValueError, "Withdrawal amount must be positive."):
            self.account.withdraw(-50.0)

    @patch('accounts.get_share_price')
    def test_buy_shares_success(self, mock_price_func):
        """Test successfully buying shares."""
        mock_price_func.return_value = 100.0
        self.account.deposit(1000.0)
        
        self.account.buy_shares('AAPL', 5, mock_price_func)
        
        # Check Cash: 1000 - (5 * 100) = 500
        self.assertEqual(self.account.cash_balance, 500.0)
        
        # Check Holdings
        self.assertIn('AAPL', self.account.holdings)
        holding = self.account.holdings['AAPL']
        self.assertEqual(holding.quantity, 5)
        self.assertEqual(holding.total_cost_basis, 500.0)
        
        # Check Transaction
        txn = self.account.transactions[1] # Index 1 is the BUY
        self.assertEqual(txn.type, 'BUY')
        self.assertEqual(txn.symbol, 'AAPL')
        self.assertEqual(txn.quantity, 5)
        self.assertEqual(txn.price, 100.0)
        self.assertEqual(txn.amount, -500.0)

    @patch('accounts.get_share_price')
    def test_buy_shares_insufficient_funds(self, mock_price_func):
        """Test buying shares with insufficient cash."""
        mock_price_func.return_value = 100.0
        self.account.deposit(400.0) # Only enough for 4 shares
        
        with self.assertRaisesRegex(ValueError, "Insufficient funds to buy shares."):
            self.account.buy_shares('AAPL', 5, mock_price_func)

    def test_buy_shares_invalid_symbol(self):
        """Test buying shares with a symbol that raises ValueError in price_func."""
        def bad_price_func(symbol):
            raise ValueError(f"Unknown symbol: {symbol}")
        
        self.account.deposit(1000.0)
        with self.assertRaisesRegex(ValueError, "Invalid symbol provided: UNKNOWN"):
            self.account.buy_shares('UNKNOWN', 10, bad_price_func)

    def test_buy_shares_invalid_quantity(self):
        """Test buying with non-positive quantity."""
        def dummy_price(s): return 100.0
        
        with self.assertRaisesRegex(ValueError, "Quantity must be positive."):
            self.account.buy_shares('AAPL', 0, dummy_price)
        
        with self.assertRaisesRegex(ValueError, "Quantity must be positive."):
            self.account.buy_shares('AAPL', -5, dummy_price)

    @patch('accounts.get_share_price')
    def test_sell_shares_full_sale(self, mock_price_func):
        """Test selling all shares of a symbol."""
        mock_price_func.return_value = 100.0
        self.account.deposit(1000.0)
        self.account.buy_shares('AAPL', 10, mock_price_func) # Cost 1000
        
        # Sell all 10 at higher price (Profit)
        mock_price_func.return_value = 150.0
        self.account.sell_shares('AAPL', 10, mock_price_func)
        
        # Cash: 0 (initial) + 1500 (sale proceeds) = 1500
        self.assertEqual(self.account.cash_balance, 1500.0)
        
        # Holdings: AAPL should be gone
        self.assertNotIn('AAPL', self.account.holdings)
        
        # Transaction
        txn = self.account.transactions[2] # Deposit, Buy, Sell
        self.assertEqual(txn.type, 'SELL')
        self.assertEqual(txn.amount, 1500.0)

    @patch('accounts.get_share_price')
    def test_sell_shares_partial_sale(self, mock_price_func):
        """Test selling part of a holding."""
        mock_price_func.return_value = 100.0
        self.account.deposit(1000.0)
        self.account.buy_shares('TSLA', 10, mock_price_func) # Cost 1000
        
        # Sell 5 shares
        mock_price_func.return_value = 120.0
        self.account.sell_shares('TSLA', 5, mock_price_func)
        
        # Cash: 0 + 600 (5 * 120)
        self.assertEqual(self.account.cash_balance, 600.0)
        
        # Holdings: 5 shares left, cost basis should be half of original (500)
        holding = self.account.holdings['TSLA']
        self.assertEqual(holding.quantity, 5)
        self.assertEqual(holding.total_cost_basis, 500.0)

    def test_sell_shares_insufficient_holdings(self):
        """Test selling more shares than owned."""
        # Manually inject a holding
        self.account.holdings['AAPL'] = ShareHolding('AAPL', 5, 500.0)
        
        def dummy_price(s): return 100.0
        with self.assertRaisesRegex(ValueError, "Insufficient shares held to sell."):
            self.account.sell_shares('AAPL', 10, dummy_price)

    def test_sell_shares_symbol_not_in_holdings(self):
        """Test selling a symbol not owned."""
        def dummy_price(s): return 100.0
        with self.assertRaisesRegex(ValueError, "Insufficient shares held to sell."):
            self.account.sell_shares('AAPL', 1, dummy_price)

    @patch('accounts.get_share_price')
    def test_get_portfolio_value(self, mock_price_func):
        """Test calculation of total portfolio value."""
        mock_price_func.return_value = 100.0
        self.account.deposit(1000.0)
        self.account.buy_shares('AAPL', 5, mock_price_func) # Cash 500, Holdings 500
        
        mock_price_func.return_value = 120.0 # Market price rises
        # Note: get_portfolio_value usually uses the price_func passed to it, 
        # but the method signature uses the passed callable.
        # However, in this test class, we are mocking the imported 'get_share_price' 
        # used internally by default or passed arguments. 
        # Let's define a specific price func for the valuation call.
        
        def rising_price_func(symbol):
            if symbol == 'AAPL': return 120.0
            raise ValueError("Unknown")
            
        val = self.account.get_portfolio_value(rising_price_func)
        # Cash (500) + Market Value (5 * 120 = 600) = 1100
        self.assertEqual(val, 1100.0)

    @patch('accounts.get_share_price')
    def test_get_profit_loss(self, mock_price_func):
        """Test PnL calculation."""
        mock_price_func.return_value = 100.0
        self.account.deposit(1000.0)
        self.account.buy_shares('AAPL', 10, mock_price_func) # All cash used, Initial Dep 1000
        
        def current_price_func(symbol):
            if symbol == 'AAPL': return 150.0
            raise ValueError("Unknown")
            
        # Portfolio Value = 10 shares * 150 = 1500 (Cash 0)
        # PnL = 1500 - 1000 (Initial) = 500
        pnl = self.account.get_profit_loss(current_price_func)
        self.assertEqual(pnl, 500.0)

    def test_get_holdings_report(self):
        """Test getting a simple dict report of holdings."""
        # Inject holdings manually
        self.account.holdings['AAPL'] = ShareHolding('AAPL', 10, 1000.0)
        self.account.holdings['TSLA'] = ShareHolding('TSLA', 5, 500.0)
        
        report = self.account.get_holdings_report()
        
        expected = {'AAPL': 10, 'TSLA': 5}
        self.assertDictEqual(report, expected)

    def test_get_transaction_history(self):
        """Test retrieving transaction history."""
        self.account.deposit(500.0)
        self.account.withdraw(100.0)
        
        history = self.account.get_transaction_history()
        
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].type, 'DEPOSIT')
        self.assertEqual(history[1].type, 'WITHDRAWAL')

    def test_private_update_holding_on_buy_new(self):
        """Test private helper _update_holding_on_buy for new symbol."""
        self.account._update_holding_on_buy('AAPL', 10, 100.0)
        
        holding = self.account.holdings['AAPL']
        self.assertEqual(holding.quantity, 10)
        self.assertEqual(holding.total_cost_basis, 1000.0)

    def test_private_update_holding_on_buy_existing(self):
        """Test private helper _update_holding_on_buy for existing symbol."""
        # Setup existing holding
        self.account.holdings['AAPL'] = ShareHolding('AAPL', 5, 500.0)
        
        # Add more
        self.account._update_holding_on_buy('AAPL', 5, 120.0)
        
        holding = self.account.holdings['AAPL']
        # New Quantity: 5 + 5 = 10
        # New Cost: 500 + (5 * 120) = 1100
        self.assertEqual(holding.quantity, 10)
        self.assertEqual(holding.total_cost_basis, 1100.0)

    def test_private_update_holding_on_sell_all(self):
        """Test private helper _update_holding_on_sell removing all shares."""
        self.account.holdings['AAPL'] = ShareHolding('AAPL', 10, 1000.0)
        
        self.account._update_holding_on_sell('AAPL', 10, 150.0)
        
        self.assertNotIn('AAPL', self.account.holdings)

    def test_private_update_holding_on_sell_partial(self):
        """Test private helper _update_holding_on_sell partial shares."""
        self.account.holdings['AAPL'] = ShareHolding('AAPL', 10, 1000.0)
        
        self.account._update_holding_on_sell('AAPL', 4, 150.0)
        
        holding = self.account.holdings['AAPL']
        # New Qty: 10 - 4 = 6
        # Cost Reduction: 1000 * (4/10) = 400
        # New Cost: 1000 - 400 = 600
        self.assertEqual(holding.quantity, 6)
        self.assertEqual(holding.total_cost_basis, 600.0)

class TestExternalFunctions(unittest.TestCase):
    """Tests for the external dependency mock implementations."""

    def test_get_share_price_known_symbols(self):
        """Test that get_share_price returns correct values for known symbols."""
        self.assertEqual(get_share_price('AAPL'), 150.00)
        self.assertEqual(get_share_price('TSLA'), 250.00)
        self.assertEqual(get_share_price('GOOGL'), 100.00)

    def test_get_share_price_unknown_symbol(self):
        """Test that get_share_price raises ValueError for unknown symbols."""
        with self.assertRaisesRegex(ValueError, "Unknown symbol: UNKNOWN"):
            get_share_price('UNKNOWN')

if __name__ == '__main__':
    unittest.main()