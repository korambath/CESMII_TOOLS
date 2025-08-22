# mcp_math_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return int(a + b)

@mcp.tool()
def subtract(a: int, b: int) -> int:
        """Subtract second number from first number."""
        return int(a - b)

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b 

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide first number by second number."""
    if b == 0:
       raise ValueError("Cannot divide by zero")
    return a / b

if __name__ == "__main__":
    print("starting mcp server stdio")
    mcp.run(transport="stdio")
