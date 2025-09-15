#!/usr/bin/env python
from agents import Agent, Runner, trace, function_tool
from openai.types.responses import ResponseTextDeltaEvent
from openai import OpenAI
from typing import Dict
import os
from dotenv import load_dotenv
import asyncio
import smtplib
from email.message import EmailMessage
import yfinance as yf

load_dotenv(override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

instructions = """ 
      You are a Market Analysis Agent specialized in retrieving current stock market data. 
      When requested, you will:
      1. Use the stock price API to get the current price for any given ticker symbol
      2. Provide accurate and up-to-date stock information
      3. Format the stock data in a clear and professional manner for further use
"""


market_analysis_agent = Agent(
        name="Market Analysis Agent",
        instructions=instructions,
        model="gpt-4o-mini"
)

@function_tool
def get_stock_price(ticker: str) -> dict:
    """
    Fetches the current (latest) price of a given stock ticker.

    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL').

    Returns:
        dict: A dictionary containing the stock price and ticker,
              or an error message if the operation fails.
    """
    try:
        stock = yf.Ticker(ticker)
        # Fetching info might raise an exception if the ticker is invalid or no data
        stock_info = stock.info

        price = stock_info.get("currentPrice")
        if price is None:
            price = "Price not available"
            error_message = f"Warning: Could not find 'currentPrice' for {ticker}. Data might be incomplete or key name changed."
        else:
            error_message = None

        return {
            "ticker": ticker,
            "price": price,
            "error": error_message
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "price": "Error fetching price",
            "error": f"An unexpected error occurred: {e}"
        }

@function_tool
def send_local_email(body: str) -> Dict[str, str]:
    """Sends a plain text email using a local SMTP server inlining the {body}."""
    sender_email = "<username>@localhost"  # Replace username with your sender address
    recipient_email = "<username>@localhost"  # Replace username with the recipient's email
    email_subject = "Agent Email from MacOS Server"
    msg = EmailMessage()
    msg['Subject'] =  email_subject
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg.set_content(body)

    try:
        # Connect to the local SMTP server (usually on localhost, port 25)
        with smtplib.SMTP('localhost', 8025) as server:
            server.send_message(msg)
        print("Email sent successfully!")
        return {"status": "success"}
    except smtplib.SMTPException as e:
        print(f"Error sending email: {e}")
        return {"status": "Error"}



# #### Get user input for stock symbol
print("Welcome to the Stock Market Email Analyzer!")
ticker_symbol = input("Please enter a stock ticker symbol (e.g., AAPL, GOOGL, TSLA): ").upper().strip()

if not ticker_symbol:
    print("No ticker symbol provided. Using AAPL as default.")
    ticker_symbol = "AAPL"

print(f"Analyzing stock: {ticker_symbol}")

# #### Convert an agent into tool

description = f"find the current stock price for the ticker symbol '{ticker_symbol}'"

market_tool = market_analysis_agent.as_tool(tool_name="market_analysis_agent", tool_description=description)

tools = [market_tool, send_local_email, get_stock_price]


instructions = """
      You are a Stock Market Analysis Manager. When someone requests stock market information, you must:
      
      1. Use the available tools to retrieve the current stock price for the requested ticker symbol
      2. Compose a professional email that includes:
         - The stock ticker symbol
         - The current stock price
         - A brief summary of the information
         - Professional formatting suitable for business communication
      3. Send the composed email using the email tool
      
      Always complete the full workflow: retrieve stock data → compose email → send email.
      Ensure all communications are professional and informative.
"""


market_analysis_manager = Agent(name="Market Analysis Manager", instructions=instructions, tools=tools, model="gpt-4o-mini")

message = f"Please provide the current stock market analysis for {ticker_symbol}. Retrieve the latest stock price and send a professional email report to the CEO with the findings."

with trace("Sales manager"):
    result = asyncio.run( Runner.run(market_analysis_manager, message))


print(result)




