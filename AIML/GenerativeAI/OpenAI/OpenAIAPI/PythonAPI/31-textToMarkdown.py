import openai
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
import os
import sys
import argparse

def print_usage():
    """
    Prints usage instructions for the text to markdown converter.
    """
    print("\n=== Text to Markdown Converter ===")
    print("This script converts plain text files to well-formatted Markdown using OpenAI's GPT model.")
    print("\nUsage:")
    print(f"  python {os.path.basename(__file__)} <input_file> <output_file>")
    print("\nArguments:")
    print("  input_file   : Path to the input text file to convert")
    print("  output_file  : Path where the Markdown file will be saved")
    print("\nExample:")
    print(f"  python {os.path.basename(__file__)} mytext.txt mytext.md")
    print("\nRequirements:")
    print("  - OPENAI_API_KEY environment variable must be set")
    print("  - Input file must exist and be readable")
    print("=====================================\n")

def text_to_markdown(input_filepath, output_filepath):
    """
    Reads a text file, sends its content to OpenAI to convert to Markdown, and writes the Markdown to a file.

    Args:
        input_filepath (str): The path to the input text file.
        output_filepath (str): The path where the Markdown file will be saved.
    """
    try:
        # Check if API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        
        client = OpenAI(api_key=api_key)
        model = "gpt-4.1"  # Using a valid model name
        
        # Check if input file exists before proceeding
        if not os.path.exists(input_filepath):
            raise FileNotFoundError(f"Input file '{input_filepath}' does not exist.")
        
        print(f"Reading content from '{input_filepath}'...")
        with open(input_filepath, 'r', encoding='utf-8') as infile:
            content = infile.read()

        prompt = (
            "Convert the following plain text to well-formatted Markdown. "
            "Preserve headings, lists, code blocks, and any structure. "
            "Use proper Markdown syntax including # for headings, * or - for lists, "
            "``` for code blocks, and appropriate formatting for emphasis.\n\n" + content
        )
        
        print("Sending request to OpenAI...")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3  # Lower temperature for more consistent formatting
        )
        markdown_content = response.choices[0].message.content

        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_filepath)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"Created directory: {output_dir}")

        print(f"Writing Markdown to '{output_filepath}'...")
        with open(output_filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(markdown_content)

        print(f"Successfully converted '{input_filepath}' to '{output_filepath}' using OpenAI.")
    except FileNotFoundError:
        print(f"Error: The file '{input_filepath}' was not found.")
        return False
    except ValueError as e:
        print(f"Configuration error: {e}")
        return False
    except PermissionError:
        print(f"Error: Permission denied when trying to write to '{output_filepath}'.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False
    
    return True

# --- How to use the function ---
if __name__ == "__main__":
    # Check if correct number of arguments are provided
    if len(sys.argv) != 3:
        print("Error: Incorrect number of arguments.")
        print_usage()
        sys.exit(1)
    
    # Parse command line arguments
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Validate file extensions
    if not input_file.strip():
        print("Error: Input file name cannot be empty.")
        sys.exit(1)
    
    if not output_file.strip():
        print("Error: Output file name cannot be empty.")
        sys.exit(1)
    
    # Suggest .md extension if not provided
    if not output_file.lower().endswith('.md'):
        print(f"Note: Output file doesn't have .md extension. Consider using '{output_file}.md'")
    
    # Display usage information
    print_usage()
    
    # Convert the file
    success = text_to_markdown(input_file, output_file)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
