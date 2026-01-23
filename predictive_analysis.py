# predictive_analysis.py
import re
import math
import pandas as pd

def parse_financial_query(query: str):
    """
    Parses financial questions and performs predictive analysis
    for savings, FDs, spendings, and future value predictions.
    """

    q = query.lower().strip()

    # --- Handle Empty Queries ---
    if not q:
        return None

    # --- Handle FD / Compound Interest Queries ---
    # Examples: "What will my 10 lakh be after 5 years at 7% interest?"
    fd_pattern = re.search(
        r"(\d+(?:\.\d+)?)\s*(lakh|lac|rs|₹)?[^0-9]*(\d+)\s*year.*?(\d+(?:\.\d+)?)\s*%?", q
    )
    if fd_pattern:
        amount = float(fd_pattern.group(1))
        if fd_pattern.group(2) in ["lakh", "lac"]:
            amount *= 100000
        years = int(fd_pattern.group(3))
        rate = float(fd_pattern.group(4))
        maturity = round(amount * ((1 + rate / 100) ** years), 2)
        return f"💰 Your ₹{amount:,.0f} will grow to approximately ₹{maturity:,.0f} after {years} years at {rate}% annual interest."

    # --- Handle Simple Interest Queries ---
    si_pattern = re.search(
        r"simple interest.*?(\d+(?:\.\d+)?)\s*(lakh|lac|rs|₹)?[^0-9]*(\d+)\s*year.*?(\d+(?:\.\d+)?)\s*%?", q
    )
    if si_pattern:
        principal = float(si_pattern.group(1))
        if si_pattern.group(2) in ["lakh", "lac"]:
            principal *= 100000
        time = int(si_pattern.group(3))
        rate = float(si_pattern.group(4))
        si = round((principal * rate * time) / 100, 2)
        total = principal + si
        return f"💸 Simple Interest: ₹{si:,.2f}\nTotal after {time} years: ₹{total:,.2f}"

    # --- Handle "Predict my next month spending" ---
    if "predict" in q and "spending" in q:
        try:
            df = pd.read_csv("data/transactions.csv")  # Example: you can make one later
            spend_trend = df["spending"].tail(6).mean()
            predicted = round(spend_trend * 1.05, 2)  # assume 5% increase
            return f"📊 Based on your recent trend, your next month's spending is estimated to be ₹{predicted:,.2f}."
        except FileNotFoundError:
            return "📈 Please upload a `transactions.csv` file with spending data to enable predictions."
        except Exception as e:
            return f"⚠️ Error during spending prediction: {e}"

    # --- Handle "What will be my account balance after X years?" ---
    if re.search(r"balance.*after.*year", q):
        num_match = re.search(r"(\d+(?:\.\d+)?)\s*year", q)
        if num_match:
            years = float(num_match.group(1))
            growth_rate = 0.05  # Assume 5% annual growth
            base_balance = 100000  # Example base balance; can be linked to user's balance
            future_balance = round(base_balance * ((1 + growth_rate) ** years), 2)
            return f"🏦 If your balance grows at 5% annually, in {years} years your balance could be around ₹{future_balance:,.2f}."

    # --- Handle "FD Maturity", "Interest amount", etc. ---
    if "fd" in q or "fixed deposit" in q or "maturity" in q:
        return "💡 Please specify the amount, duration (in years), and interest rate for accurate FD maturity prediction."

    # --- Handle "Investment Growth" ---
    if "invest" in q or "investment" in q:
        invest_match = re.search(r"(\d+(?:\.\d+)?)\s*(lakh|lac|rs|₹)?", q)
        if invest_match:
            amount = float(invest_match.group(1))
            if invest_match.group(2) in ["lakh", "lac"]:
                amount *= 100000
            rate = 0.07
            years = 10
            maturity = round(amount * ((1 + rate) ** years), 2)
            return f"📈 If you invest ₹{amount:,.0f} for 10 years at 7% annual return, it could grow to ₹{maturity:,.0f}."

    # --- If No Match ---
    return None
