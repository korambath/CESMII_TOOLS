import anthropic
import os
from dotenv import load_dotenv
import anthropic
import json
import requests
from typing import Optional, Dict, Any
import rich
from datetime import datetime
import pytz
from timezonefinder import TimezoneFinder
import random
import hashlib


# 1. Load environment variables from the .env file
load_dotenv()

# 2. Get the API key from the environment variable
api_key = os.getenv("ANTHROPIC_API_KEY")

# Check if the API key was loaded successfully
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in .env file.")

# 3. Initialize the Anthropic client with the API key
client = anthropic.Anthropic(
    api_key=api_key,
)

# Initialize an empty shopping cart
shopping_cart = []
print("Initial cart:", shopping_cart)

# Global product price database for consistent pricing
product_prices = {}

def get_product_price(product_id: str) -> float:
    """
    Gets or generates a consistent price for a product based on its ID.
    
    Uses the product ID as a seed to ensure the same product always has the same price.
    Different product categories have different price ranges for realism.
    
    Args:
        product_id (str): The unique product identifier
        
    Returns:
        float: The price for the product (rounded to 2 decimal places)
    """
    global product_prices
    
    # Return existing price if already generated
    if product_id in product_prices:
        return product_prices[product_id]
    
    # Create a deterministic seed from product ID
    seed = int(hashlib.md5(product_id.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    
    # Determine price range based on product ID patterns
    product_id_upper = product_id.upper()
    
    if any(keyword in product_id_upper for keyword in ['LAPTOP', 'COMPUTER', 'PC']):
        # Laptops/Computers: $799 - $2499
        price = rng.uniform(799.00, 2499.00)
    elif any(keyword in product_id_upper for keyword in ['PHONE', 'IPHONE', 'SMARTPHONE']):
        # Phones: $299 - $1199
        price = rng.uniform(299.00, 1199.00)
    elif any(keyword in product_id_upper for keyword in ['TABLET', 'IPAD']):
        # Tablets: $199 - $899
        price = rng.uniform(199.00, 899.00)
    elif any(keyword in product_id_upper for keyword in ['HEADPHONE', 'EARPHONE', 'EARBUDS']):
        # Audio devices: $29 - $399
        price = rng.uniform(29.00, 399.00)
    elif any(keyword in product_id_upper for keyword in ['MOUSE', 'KEYBOARD', 'WEBCAM']):
        # Peripherals: $19 - $149
        price = rng.uniform(19.00, 149.00)
    elif any(keyword in product_id_upper for keyword in ['CABLE', 'CHARGER', 'ADAPTER']):
        # Accessories: $9 - $79
        price = rng.uniform(9.00, 79.00)
    elif any(keyword in product_id_upper for keyword in ['CASE', 'COVER', 'SCREEN']):
        # Cases/Covers: $12 - $59
        price = rng.uniform(12.00, 59.00)
    elif any(keyword in product_id_upper for keyword in ['APPLE', 'ORANGE', 'GRAPES', 'BANANA', 'ONION', 'POTATO', 'PEACH' 'BREAD']):
        # Cases/Covers: $2 - $5
        price = rng.uniform(2.00, 5.00)
    else:
        # Generic products: $15 - $199
        price = rng.uniform(15.00, 199.00)
    
    # Round to 2 decimal places and store
    price = round(price, 2)
    product_prices[product_id] = price
    
    return price


def add_to_cart(products: list) -> dict:
    """
    Adds products to the shopping cart or updates their quantity if they already exist.
    
    This function processes a list of products and either adds new items to the cart
    or increments the quantity of existing items. Each product must have a valid
    product ID and a positive quantity.

    Args:
        products (list): A list of dictionaries with 'productId' and 'quantity' keys.
                        Example: [{"productId": "PROD001", "quantity": 2}]

    Returns:
        dict: Status response containing:
            - status: "success" or "error"
            - message: Description of the operation
            - cart: Current cart contents
            - cart_total_items: Total number of unique products
            - error_details: List of any errors encountered (if applicable)
    """
    global shopping_cart
    
    if not isinstance(products, list):
        return {
            "status": "error", 
            "message": "Products must be provided as a list",
            "cart": shopping_cart,
            "cart_total_items": len(shopping_cart)
        }
    
    if not products:
        return {
            "status": "error", 
            "message": "No products provided",
            "cart": shopping_cart,
            "cart_total_items": len(shopping_cart)
        }
    
    added_products = []
    errors = []
    
    for i, product in enumerate(products):
        if not isinstance(product, dict):
            errors.append(f"Product at index {i} must be a dictionary")
            continue
            
        product_id = product.get('productId')
        quantity = product.get('quantity', 1)
        
        # Validate product ID
        if not isinstance(product_id, str) or not product_id.strip():
            errors.append(f"Product at index {i}: productId must be a non-empty string")
            continue
            
        # Validate quantity
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            errors.append(f"Product at index {i}: quantity must be a positive number")
            continue
        
        # Convert to integer if it's a valid number
        quantity = int(quantity)
        product_id = product_id.strip()

        # Check if product already exists in cart
        product_found = False
        for item in shopping_cart:
            if item.get('product_id') == product_id:
                old_quantity = item['quantity']
                item['quantity'] += quantity
                # Get price for display (should already exist)
                price = item.get('price_per_unit', get_product_price(product_id))
                added_products.append(f"{product_id} (updated: {old_quantity} → {item['quantity']}) @ ${price:.2f}")
                product_found = True
                break

        if not product_found:
            # Get price for new product
            price = get_product_price(product_id)
            # Add new product to cart with price
            shopping_cart.append({
                'product_id': product_id, 
                'quantity': quantity,
                'price_per_unit': price
            })
            added_products.append(f"{product_id} (new: {quantity}) @ ${price:.2f}")

    # Calculate total cost of added items for response
    total_cost_added = 0.0
    for i, product in enumerate(products):
        if i < len(added_products):  # Only count successfully added products
            product_id = product.get('productId', '').strip()
            quantity = int(product.get('quantity', 1))
            price = get_product_price(product_id)
            total_cost_added += quantity * price

    # Prepare response
    if errors and not added_products:
        return {
            "status": "error",
            "message": "Failed to add any products to cart",
            "cart": shopping_cart,
            "cart_total_items": len(shopping_cart),
            "error_details": errors
        }
    elif errors and added_products:
        return {
            "status": "partial_success",
            "message": f"Added {len(added_products)} product(s) (${total_cost_added:.2f} total), but encountered {len(errors)} error(s)",
            "cart": shopping_cart,
            "cart_total_items": len(shopping_cart),
            "added_products": added_products,
            "total_cost_added": total_cost_added,
            "error_details": errors
        }
    else:
        return {
            "status": "success",
            "message": f"Successfully added {len(added_products)} product(s) to cart (${total_cost_added:.2f} total)",
            "cart": shopping_cart,
            "cart_total_items": len(shopping_cart),
            "added_products": added_products,
            "total_cost_added": total_cost_added
        }


def remove_from_cart(products: list) -> dict:
    """
    Removes specified quantities of products from the shopping cart by their product IDs.
    
    This function can remove specific quantities of products or remove them entirely.
    If the quantity to remove is greater than or equal to the current quantity,
    the product will be completely removed from the cart. If removing a partial
    quantity, the remaining amount will stay in the cart.

    Args:
        products (list): A list of dictionaries with 'productId' and optional 'quantity' keys.
                        If 'quantity' is not specified, the entire product will be removed.
                        Example: [{"productId": "PROD001", "quantity": 2}, {"productId": "PROD002"}]

    Returns:
        dict: Status response containing:
            - status: "success", "partial_success", or "error"
            - message: Description of the operation
            - cart: Updated cart contents
            - cart_total_items: Total number of unique products remaining
            - removed_products: List of products with removal details
            - not_found_products: List of product IDs that weren't in the cart
            - error_details: List of any validation errors
    """
    global shopping_cart
    
    if not isinstance(products, list):
        return {
            "status": "error",
            "message": "Products must be provided as a list",
            "cart": shopping_cart,
            "cart_total_items": len(shopping_cart)
        }
    
    if not products:
        return {
            "status": "error",
            "message": "No products provided",
            "cart": shopping_cart,
            "cart_total_items": len(shopping_cart)
        }
    
    # Process and validate input
    valid_removals = []
    invalid_items = []
    
    for i, product in enumerate(products):
        # Handle both string (product ID only) and dict (product ID + quantity) formats
        if isinstance(product, str):
            product_id = product.strip()
            quantity_to_remove = None  # Remove all
            if not product_id:
                invalid_items.append(f"Product at index {i} is empty")
                continue
        elif isinstance(product, dict):
            product_id = product.get('productId')
            quantity_to_remove = product.get('quantity', None)
            
            # Validate product ID
            if not isinstance(product_id, str) or not product_id.strip():
                invalid_items.append(f"Product at index {i}: productId must be a non-empty string")
                continue
            
            product_id = product_id.strip()
            
            # Validate quantity if provided
            if quantity_to_remove is not None:
                if not isinstance(quantity_to_remove, (int, float)) or quantity_to_remove <= 0:
                    invalid_items.append(f"Product at index {i}: quantity must be a positive number")
                    continue
                quantity_to_remove = int(quantity_to_remove)
        else:
            invalid_items.append(f"Product at index {i} must be a string (product ID) or dict (with productId and optional quantity)")
            continue
        
        valid_removals.append({
            'product_id': product_id,
            'quantity_to_remove': quantity_to_remove
        })
    
    if invalid_items:
        return {
            "status": "error",
            "message": "Invalid products provided",
            "cart": shopping_cart,
            "cart_total_items": len(shopping_cart),
            "error_details": invalid_items
        }
    
    # Process removals
    removed_products = []
    not_found_products = []
    
    for removal in valid_removals:
        product_id = removal['product_id']
        quantity_to_remove = removal['quantity_to_remove']
        
        # Find the product in cart
        product_found = False
        for i, item in enumerate(shopping_cart):
            if item.get('product_id') == product_id:
                product_found = True
                current_quantity = item.get('quantity', 0)
                
                if quantity_to_remove is None or quantity_to_remove >= current_quantity:
                    # Remove entire product
                    shopping_cart.pop(i)
                    removed_products.append({
                        'product_id': product_id,
                        'removed_quantity': current_quantity,
                        'action': 'completely_removed'
                    })
                else:
                    # Remove partial quantity
                    item['quantity'] -= quantity_to_remove
                    removed_products.append({
                        'product_id': product_id,
                        'removed_quantity': quantity_to_remove,
                        'remaining_quantity': item['quantity'],
                        'action': 'partially_removed'
                    })
                break
        
        if not product_found:
            not_found_products.append(product_id)
    
    # Prepare response
    if not removed_products and not_found_products:
        return {
            "status": "error",
            "message": "No products were removed (none found in cart)",
            "cart": shopping_cart,
            "cart_total_items": len(shopping_cart),
            "not_found_products": not_found_products
        }
    elif removed_products and not_found_products:
        return {
            "status": "partial_success",
            "message": f"Processed {len(removed_products)} product(s), but {len(not_found_products)} were not found in cart",
            "cart": shopping_cart,
            "cart_total_items": len(shopping_cart),
            "removed_products": removed_products,
            "not_found_products": not_found_products
        }
    else:
        return {
            "status": "success",
            "message": f"Successfully processed removal of {len(removed_products)} product(s)",
            "cart": shopping_cart,
            "cart_total_items": len(shopping_cart),
            "removed_products": removed_products
        }

def get_order_summary() -> dict:
    """
    Generates a comprehensive summary of all products in the shopping cart.
    
    This function creates a formatted summary with structured data about the cart.
    It provides both human-readable text and detailed cart statistics.

    Returns:
        dict: Comprehensive summary containing:
            - status: "success" 
            - summary_text: Human-readable formatted summary
            - cart: Raw cart data
            - cart_statistics: Summary statistics about the cart
    """
    global shopping_cart
    
    # English-only text templates
    translations = {
        'title': "🛒 Shopping Cart Summary",
        'empty_message': "Your shopping cart is empty.",
        'product_line': "• {product_id} - Qty: {quantity} @ ${price:.2f} each = ${line_total:.2f}",
        'subtotal_line': "\n💰 Pricing Summary:",
        'grand_total': "Grand Total: ${total:.2f}",
        'total_line': "\n📊 Cart Statistics:",
        'unique_products': "Unique products: {count}",
        'total_items': "Total items: {count}",
        'average_price': "Average price per item: ${avg:.2f}",
        'footer': "\nThank you for shopping with us!"
    }

    # Calculate cart statistics
    total_items = sum(item.get('quantity', 0) for item in shopping_cart)
    unique_products = len(shopping_cart)
    grand_total = 0.0
    
    # Build summary
    summary_lines = [translations['title']]
    
    if not shopping_cart:
        summary_lines.append(translations['empty_message'])
    else:
        # Add each product with pricing
        for item in shopping_cart:
            product_id = item.get('product_id', 'Unknown Product')
            quantity = item.get('quantity', 0)
            # Get price (handle legacy cart items without price)
            price = item.get('price_per_unit')
            if price is None:
                price = get_product_price(product_id)
                item['price_per_unit'] = price  # Update cart item for consistency
            
            line_total = quantity * price
            grand_total += line_total
            
            summary_lines.append(translations['product_line'].format(
                product_id=product_id,
                quantity=quantity,
                price=price,
                line_total=line_total
            ))
        
        # Add pricing summary
        summary_lines.append(translations['subtotal_line'])
        summary_lines.append(translations['grand_total'].format(total=grand_total))
        
        # Add statistics
        summary_lines.append(translations['total_line'])
        summary_lines.append(translations['unique_products'].format(count=unique_products))
        summary_lines.append(translations['total_items'].format(count=total_items))
        if total_items > 0:
            avg_price = grand_total / total_items
            summary_lines.append(translations['average_price'].format(avg=avg_price))
        summary_lines.append(translations['footer'])
    
    return {
        "status": "success",
        "summary_text": "\n".join(summary_lines),
        "cart": shopping_cart,
        "cart_statistics": {
            "unique_products": unique_products,
            "total_items": total_items,
            "grand_total": grand_total,
            "average_price_per_item": round(grand_total / total_items, 2) if total_items > 0 else 0.0,
            "is_empty": len(shopping_cart) == 0
        }
    }

add_to_cart_tool = { 
    "name": "add_to_cart",
    "description": "Adds one or more products to the shopping cart with specified quantities and automatic pricing. If a product already exists in the cart, its quantity will be increased by the specified amount while maintaining the original price. Each product gets a consistent price based on its ID and category. This tool validates product IDs and quantities, provides detailed feedback about successful additions, total costs, and any errors encountered. Use this when customers want to add items to their cart for purchase.",
    "input_schema": {
        "type": "object",
        "properties": {
            "products": {
                "description": "An array of products to be added to the cart. Each product must include a unique product ID and the desired quantity to add.",
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "productId": {
                            "type": "string",
                            "description": "The unique identifier of the product to be added to the cart. This must be a non-empty string that corresponds to a valid product in the store's inventory."
                        },
                        "quantity": {
                            "type": "number",
                            "description": "The number of units of the product to be added to the cart. This must be a positive integer greater than 0."
                        }
                    },
                    "required": ["productId", "quantity"]
                }
            }
        },
        "required": ["products"]
    }
}
remove_from_cart_tool = {
    "name": "remove_from_cart",
    "description": "Removes specific quantities of products from the shopping cart or removes products entirely. This tool supports both partial removal (reducing quantity) and complete removal of products. If a quantity is specified and it's less than the current quantity in the cart, only that amount will be removed and the product will remain in the cart with the reduced quantity. If no quantity is specified or the quantity is greater than or equal to the current quantity, the entire product will be removed from the cart.",
    "input_schema": {
        "type": "object",
        "properties": {
          "products": {
              "description": "An array of products to be removed from the cart. Each item can be either a simple string (product ID for complete removal) or an object with productId and optional quantity for partial removal.",
              "type": "array",
              "items": {
                  "oneOf": [
                      {
                          "type": "string",
                          "description": "A product ID string for complete removal of the product from cart"
                      },
                      {
                          "type": "object",
                          "properties": {
                              "productId": {
                                  "type": "string",
                                  "description": "The unique identifier of the product to remove from the cart"
                              },
                              "quantity": {
                                  "type": "number",
                                  "description": "The number of units to remove. If not specified or greater than current quantity, the entire product will be removed. Must be a positive integer."
                              }
                          },
                          "required": ["productId"]
                      }
                  ]
              }
          }
        },
        "required": ["products"]
    }
}
get_order_summary_tool = {
    "name": "get_order_summary",
    "description": "Generates a comprehensive summary of the current shopping cart contents including product details, quantities, individual prices, line totals, and grand total. The summary includes pricing statistics such as average price per item and overall cart value. The summary is formatted in a human-readable way in English with proper currency formatting. Use this when customers want to review their cart contents, check pricing details, see total costs, or get a formatted overview before proceeding to checkout.",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": []
    }
}

# List of all available tools
available_tools = [add_to_cart_tool, remove_from_cart_tool, get_order_summary_tool]


def process_user_request(user_input):
    """
    Process user request for weather or stock information using Claude and available tools
    """
    messages = [{"role": "user", "content": user_input}]

    response = client.messages.create(
        model="claude-opus-4-1-20250805",
        max_tokens=1024,
        tools=available_tools,
        messages=messages
    )

    print(f"\n=== Processing Request: {user_input} ===")
    
    # Check if Claude wants to use a tool
    if response.stop_reason == "tool_use":
        print("🔧 Processing tool calls...")
        
        # Add assistant's response to conversation
        messages.append({"role": "assistant", "content": response.content})
        
        # Process each tool use in the response
        tool_results = []
        for content_block in response.content:
            if content_block.type == "tool_use":
                tool_name = content_block.name
                tool_input = content_block.input
                tool_use_id = content_block.id
                
                print(f" Using tool: {tool_name}")
                print(f" Tool input: {tool_input}")
                
                # Call the appropriate function
                if tool_name == "add_to_cart":
                    # add to cart
                    print(f"🛒 Adding products to cart: {tool_input.get('products', [])}")
                    result = add_to_cart(tool_input["products"])
                elif tool_name == "remove_from_cart":
                    # remove from cart
                    print(f"🗑️ Removing products from cart: {tool_input.get('products', [])}")
                    result = remove_from_cart(tool_input["products"])
                elif tool_name == "get_order_summary":
                    # get order summary
                    print(f"📋 Getting order summary")
                    result = get_order_summary()
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": json.dumps(result)
                })
        
        # Send tool results back to Claude
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
            
            final_response = client.messages.create(
                model="claude-opus-4-1-20250805",
                max_tokens=1024,
                tools=available_tools,
                messages=messages
            )
            
            print("\n📊 Response:")
            for content_block in final_response.content:
                if content_block.type == "text":
                    print(content_block.text)
    else:
        print("\n💬 Claude responded without using tools:")
        # Just print the regular response
        for content_block in response.content:
            if content_block.type == "text":
                print(content_block.text)

def main():
    """
    Main function that runs the interactive assistant loop
    """
    print("🛒 Welcome to the AI Shopping Cart Assistant!")
    print("\n📝 Example queries you can try:")
    print("  • 'Add 3 laptops and 2 wireless mice to my cart'")
    print("  • 'Put 5 iPhone cases, 1 tablet, and 3 phone chargers in the cart'")
    print("  • 'Remove 2 laptops from my cart'")
    print("  • 'Remove all wireless mice from the cart'")
    print("  • 'Show me what's in my cart' or 'Give me a cart summary'")
    print("  • 'Add 4 headphones, then remove 1 headphone, then show summary'")
    print("\n💡 You can also use product IDs like:")
    print("  • 'Add LAPTOP001 quantity 2 and MOUSE003 quantity 1 to cart'")
    print("  • 'Remove LAPTOP001 quantity 1 from cart'")
    print("\nType 'exit' to quit.\n")
    #user_input = input("What would you like to do?. Type 'quit' to exit: ")
    #if user_input.lower() == 'quit' or user_input.lower() == 'exit':
    #    break
    
    while True:
        try:
            # Get user input
            user_input = input("Enter your question (or 'exit' to quit): ").strip()
            
            # Check for exit condition
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Thanks for using the AI Assistant! Goodbye!")
                break
            
            # Skip empty inputs
            if not user_input:
                print("⚠️  Please enter a valid question.")
                continue
            
            # Process the user request
            process_user_request(user_input)
            print("\n" + "="*50)
            
        except KeyboardInterrupt:
            print("\n\n👋 Thanks for using the AI Assistant! Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Please try again.")

if __name__ == "__main__":
    main()


