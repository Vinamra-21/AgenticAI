import gradio as gr
from accounts import Account, get_share_price

# Global state to hold the single user account instance
account_instance = None

# --- UI Event Handlers ---

def create_account(initial_deposit):
    global account_instance
    try:
        # We create a generic ID for the demo
        account_instance = Account(account_id="demo_user", initial_deposit=initial_deposit)
        return f"Account created successfully with initial deposit: ${initial_deposit:.2f}"
    except Exception as e:
        return f"Error creating account: {str(e)}"

def deposit_funds(amount):
    global account_instance
    if not account_instance:
        return "Please create an account first."
    try:
        account_instance.deposit(amount)
        return f"Deposited ${amount:.2f}. New Balance: ${account_instance.cash_balance:.2f}"
    except Exception as e:
        return f"Error: {str(e)}"

def withdraw_funds(amount):
    global account_instance
    if not account_instance:
        return "Please create an account first."
    try:
        account_instance.withdraw(amount)
        return f"Withdrew ${amount:.2f}. New Balance: ${account_instance.cash_balance:.2f}"
    except Exception as e:
        return f"Error: {str(e)}"

def buy_shares(symbol, quantity):
    global account_instance
    if not account_instance:
        return "Please create an account first."
    try:
        account_instance.buy_shares(symbol, quantity, get_share_price)
        price = get_share_price(symbol)
        cost = price * quantity
        return f"Bought {quantity} shares of {symbol} at ${price:.2f} (Total: ${cost:.2f}). Cash Balance: ${account_instance.cash_balance:.2f}"
    except Exception as e:
        return f"Error: {str(e)}"

def sell_shares(symbol, quantity):
    global account_instance
    if not account_instance:
        return "Please create an account first."
    try:
        account_instance.sell_shares(symbol, quantity, get_share_price)
        price = get_share_price(symbol)
        proceeds = price * quantity
        return f"Sold {quantity} shares of {symbol} at ${price:.2f} (Total: ${proceeds:.2f}). Cash Balance: ${account_instance.cash_balance:.2f}"
    except Exception as e:
        return f"Error: {str(e)}"

def update_reports():
    global account_instance
    if not account_instance:
        return "No account created.", "N/A", "N/A", "N/A", "N/A"
    
    # Calculate values
    portfolio_val = account_instance.get_portfolio_value(get_share_price)
    profit_loss = account_instance.get_profit_loss(get_share_price)
    holdings = account_instance.get_holdings_report()
    
    # Format holdings for display
    holdings_str = ""
    if holdings:
        for sym, qty in holdings.items():
            holdings_str += f"{sym}: {qty} shares\n"
    else:
        holdings_str = "No holdings."

    # Format transaction history
    history = account_instance.get_transaction_history()
    history_str = ""
    if history:
        for txn in history:
            desc = f"[{txn.timestamp.strftime('%H:%M:%S')}] {txn.type}: "
            if txn.symbol:
                desc += f"{txn.quantity} {txn.symbol} @ ${txn.price:.2f} "
            desc += f"Amount: ${txn.amount:.2f}"
            history_str += desc + "\n"
    else:
        history_str = "No transactions."

    # Current cash
    cash = account_instance.cash_balance

    return (
        f"${portfolio_val:.2f}",
        f"${profit_loss:.2f}",
        f"${cash:.2f}",
        holdings_str,
        history_str
    )

# --- Gradio Layout ---

with gr.Blocks(title="Trading Simulator Demo") as demo:
    gr.Markdown("# Simple Trading Simulation Account")
    gr.Markdown("This is a prototype demonstrating the `Account` class logic. Assume a single user session.")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 1. Account Management")
            initial_dep = gr.Number(label="Initial Deposit", value=1000)
            btn_create = gr.Button("Create / Reset Account", variant="primary")
            msg_create = gr.Textbox(label="Account Status", interactive=False)
            
            gr.Markdown("### 2. Fund Operations")
            with gr.Row():
                dep_amt = gr.Number(label="Deposit Amount", value=100)
                btn_deposit = gr.Button("Deposit")
            with gr.Row():
                wdr_amt = gr.Number(label="Withdraw Amount", value=100)
                btn_withdraw = gr.Button("Withdraw")
            msg_funds = gr.Textbox(label="Fund Operations Log", interactive=False)

        with gr.Column(scale=1):
            gr.Markdown("### 3. Trading Operations")
            with gr.Row():
                buy_sym = gr.Dropdown(label="Symbol", choices=["AAPL", "TSLA", "GOOGL"], value="AAPL")
                buy_qty = gr.Number(label="Quantity", value=10)
                btn_buy = gr.Button("Buy Shares")
            with gr.Row():
                sell_sym = gr.Dropdown(label="Symbol", choices=["AAPL", "TSLA", "GOOGL"], value="AAPL")
                sell_qty = gr.Number(label="Quantity", value=5)
                btn_sell = gr.Button("Sell Shares")
            msg_trade = gr.Textbox(label="Trade Operations Log", interactive=False)

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 4. Portfolio Reporting")
            btn_refresh = gr.Button("Refresh Reports", variant="secondary")
            
            with gr.Row():
                val_val = gr.Textbox(label="Total Portfolio Value (Cash + Shares)")
                val_pl = gr.Textbox(label="Profit / Loss (vs Initial Deposit)")
                val_cash = gr.Textbox(label="Cash Balance")

            val_holdings = gr.Textbox(label="Current Holdings", lines=5)
            val_history = gr.Textbox(label="Transaction History", lines=8)

    # --- Event Wiring ---
    
    # Account Creation
    btn_create.click(create_account, inputs=initial_dep, outputs=msg_create)
    
    # Fund Operations
    btn_deposit.click(deposit_funds, inputs=dep_amt, outputs=msg_funds)
    btn_withdraw.click(withdraw_funds, inputs=wdr_amt, outputs=msg_funds)
    
    # Trading
    btn_buy.click(buy_shares, inputs=[buy_sym, buy_qty], outputs=msg_trade)
    btn_sell.click(sell_shares, inputs=[sell_sym, sell_qty], outputs=msg_trade)
    
    # Reporting
    btn_refresh.click(update_reports, 
                      inputs=None, 
                      outputs=[val_val, val_pl, val_cash, val_holdings, val_history])
    
    # Auto-refresh reports on any action
    for btn in [btn_create, btn_deposit, btn_withdraw, btn_buy, btn_sell]:
        btn.click(update_reports, inputs=None, outputs=[val_val, val_pl, val_cash, val_holdings, val_history])

if __name__ == "__main__":
    demo.launch()