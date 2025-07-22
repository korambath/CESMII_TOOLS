# create_shapes_image.py
from PIL import Image, ImageDraw

def create_image_with_shapes(filename="shapes_image.png"):
    """
    Creates an image with a few polygons and a circle and saves it to a file.
    """
    # Define image properties
    width, height = 600, 400
    background_color = "lightcyan"

    # Create a new blank image with a specified background color
    # 'RGB' mode is for standard 24-bit color images
    image = Image.new("RGB", (width, height), background_color)

    # Create a drawing context to draw on the image
    draw = ImageDraw.Draw(image)

    # --- Draw a Circle ---
    # The circle is drawn as an ellipse within a bounding box [x0, y0, x1, y1].
    # For a perfect circle, the width and height of the box should be equal.
    circle_bbox = [50, 50, 200, 200]
    draw.ellipse(circle_bbox, fill="coral", outline="darkred")

    # --- Draw a Triangle (Polygon with 3 vertices) ---
    # The polygon is defined by a sequence of (x, y) tuples for its vertices.
    triangle_points = [(250, 50), (350, 200), (150, 200)]
    draw.polygon(triangle_points, fill="mediumseagreen", outline="darkgreen")

    # --- Draw a Rectangle ---
    # You can use the dedicated rectangle method with a bounding box.
    rectangle_bbox = [300, 250, 550, 350]
    draw.rectangle(rectangle_bbox, fill="gold", outline="orange")
    
    # --- Draw a Pentagon (Polygon with 5 vertices) ---
    pentagon_points = [(75, 250), (125, 250), (150, 300), (100, 350), (50, 300)]
    draw.polygon(pentagon_points, fill="mediumpurple", outline="indigo")

    # Save the final image to a file
    try:
        image.save(filename)
        print(f"Successfully created and saved image as '{filename}'")
    except IOError as e:
        print(f"Error saving image: {e}")

    # Optional: To display the image directly if you have a viewer configured
    # image.show()

if __name__ == "__main__":
    create_image_with_shapes()


