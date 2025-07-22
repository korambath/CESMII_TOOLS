from PIL import Image, ImageDraw, ImageFont
import random

def create_cartoon_for_person(filename="person_cartoon.png"):
    """
    Creates a fun, cartoon-style image with the name "Person".
    """
    # Image properties
    width, height = 800, 400
    background_color = "skyblue"

    # Create a new image
    image = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(image)

    # --- Add some fun background shapes (like confetti) ---
    for _ in range(150):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        # Make confetti circles of different sizes
        size = random.randint(5, 25)
        x2 = x1 + size
        y2 = y1 + size
        fill_color = random.choice(["gold", "lightpink", "palegreen", "violet"])
        draw.ellipse((x1, y1, x2, y2), fill=fill_color, outline=None)

    # --- Draw the name in the center ---
    text = "Your Name"
    font_size = 70
    font_color = "navy"

    # Try to load a nice font.
    # For best results, download a free cartoonish font like "Luckiest Guy" from Google Fonts,
    # and save it as 'LuckiestGuy-Regular.ttf' in the same directory as this script.
    font_name = "LuckiestGuy-Regular.ttf"
    try:
        font = ImageFont.truetype(font_name, font_size)
    except IOError:
        print(f"Warning: Font '{font_name}' not found. Falling back to a system font.")
        try:
            # Fallback to a common system font
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            print("Warning: 'arial.ttf' also not found. Using the basic default font.")
            font = ImageFont.load_default()

    # Calculate text size and position to center it
    # Use textbbox for modern Pillow, which is more accurate
    if hasattr(draw, 'textbbox'):
        text_box = draw.textbbox((0, 0), text, font=font)
        text_width = text_box[2] - text_box[0]
        text_height = text_box[3] - text_box[1]
    else: # Fallback for older Pillow versions
        text_width = draw.textlength(text, font=font)
        text_height = font_size # Approximation

    text_x = (width - text_width) / 2
    text_y = (height - text_height) / 2

    # Add a simple shadow effect for the text for better readability
    shadow_offset = 3
    draw.text((text_x + shadow_offset, text_y + shadow_offset), text, font=font, fill="black")

    # Draw the main text
    draw.text((text_x, text_y), text, font=font, fill=font_color)

    # --- Add a simple cartoon sun in the corner ---
    draw.ellipse([width - 180, 40, width - 40, 180], fill="yellow", outline="orange", width=5)

    # Save the image
    try:
        image.save(filename)
        print(f"Successfully created cartoon image as '{filename}'")
    except Exception as e:
        print(f"Error saving image: {e}")

if __name__ == "__main__":
    create_cartoon_for_person()


