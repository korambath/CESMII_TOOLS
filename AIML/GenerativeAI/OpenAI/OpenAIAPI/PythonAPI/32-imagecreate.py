from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Create a simple test image
img = Image.new('RGB', (400, 300), color='lightblue')
draw = ImageDraw.Draw(img)

# Add some text and shapes
draw.rectangle([50, 50, 350, 250], outline='blue', width=3)
draw.ellipse([100, 80, 200, 180], fill='yellow', outline='orange', width=2)
draw.text((120, 200), 'Hello Vision AI!', fill='black')
draw.text((120, 220), 'This is a test image', fill='darkblue')

img.save('test_image.png')
print('Test image created: test_image.png')


