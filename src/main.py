import argparse
import os
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import numpy as np
from stl import mesh

# Configuration Constants
THICKNESS_SCALE = [0.6, 3.0]
MAX_PRINT_SIDE = 150
CONTRAST = 1.2
GAUSSIAN_BLUR_RADIUS = 1


def process_image(image_path):
    # Loads and preprocesses the image to a grayscale inverted array.
    with Image.open(image_path) as img:
        # Contrast enhancement
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(CONTRAST)

        # Apply blur to smooth transitions
        img = img.filter(ImageFilter.GaussianBlur(radius=GAUSSIAN_BLUR_RADIUS))

        # Convert to grayscale and invert
        # Invert so light parts are thinner (lower Z) and dark parts are thicker (higher Z)
        img = ImageOps.invert(img.convert("L"))
        return np.asarray(img)


def create_lithophane_mesh(image_array, thickness_range, max_side):
    # Generates a 3D mesh from the grayscale image array.
    rows, cols = image_array.shape
    num_pixels = rows * cols

    # Calculate scaling to fit within max_side
    scaling_factor = max_side / max(rows, cols)

    # Normalize image array to the thickness range
    min_val, max_val = image_array.min(), image_array.max()
    if max_val == min_val:
        height_map = np.full(image_array.shape, thickness_range[0])
    else:
        height_map = thickness_range[0] + (
            (thickness_range[1] - thickness_range[0])
            * (image_array.astype(float) - min_val)
            / (max_val - min_val)
        )

    # Generate grid coordinates
    x = np.arange(rows) * scaling_factor
    y = np.arange(cols) * scaling_factor
    X, Y = np.meshgrid(x, y, indexing="ij")

    # Create vertices for top and bottom surfaces
    # Top vertices (Z from height map)
    top_vertices = np.dstack((X, Y, height_map)).reshape(-1, 3)
    # Bottom vertices (Z = 0)
    bottom_vertices = np.dstack((X, Y, np.zeros_like(height_map))).reshape(-1, 3)

    all_vertices = np.vstack((top_vertices, bottom_vertices))

    # Generate triangles for top and bottom surfaces
    # Helper to get vertex indices
    idx = np.arange(num_pixels).reshape(rows, cols)
    
    # Surface triangles (top and bottom)
    # Using slicing for vectorization
    tl = idx[:-1, :-1].ravel()  # top-left
    tr = idx[:-1, 1:].ravel()   # top-right
    bl = idx[1:, :-1].ravel()   # bottom-left
    br = idx[1:, 1:].ravel()    # bottom-right

    # Top surface triangles
    top_tri1 = np.column_stack((tl, bl, tr))
    top_tri2 = np.column_stack((tr, bl, br))
    top_triangles = np.vstack((top_tri1, top_tri2))

    # Bottom surface triangles (inverted orientation)
    bottom_tri1 = np.column_stack((tl + num_pixels, tr + num_pixels, bl + num_pixels))
    bottom_tri2 = np.column_stack((tr + num_pixels, br + num_pixels, bl + num_pixels))
    bottom_triangles = np.vstack((bottom_tri1, bottom_tri2))

    # Side triangles
    # Sides: Up (row 0), Down (row -1), Left (col 0), Right (col -1)
    
    # side_up: row 0, across cols
    up_idx = idx[0, :-1]
    up_next = idx[0, 1:]
    side_up_tri1 = np.column_stack((up_idx, up_next, up_idx + num_pixels))
    side_up_tri2 = np.column_stack((up_next, up_next + num_pixels, up_idx + num_pixels))
    
    # side_down: row -1, across cols
    down_idx = idx[-1, :-1]
    down_next = idx[-1, 1:]
    side_down_tri1 = np.column_stack((down_idx, down_idx + num_pixels, down_next))
    side_down_tri2 = np.column_stack((down_next, down_idx + num_pixels, down_next + num_pixels))

    # side_left: col 0, across rows
    left_idx = idx[:-1, 0]
    left_next = idx[1:, 0]
    side_left_tri1 = np.column_stack((left_idx, left_idx + num_pixels, left_next))
    side_left_tri2 = np.column_stack((left_next, left_idx + num_pixels, left_next + num_pixels))

    # side_right: col -1, across rows
    right_idx = idx[:-1, -1]
    right_next = idx[1:, -1]
    side_right_tri1 = np.column_stack((right_idx, right_next, right_idx + num_pixels))
    side_right_tri2 = np.column_stack((right_next, right_next + num_pixels, right_idx + num_pixels))

    all_triangles = np.vstack((
        top_triangles, 
        bottom_triangles, 
        side_up_tri1, side_up_tri2,
        side_down_tri1, side_down_tri2,
        side_left_tri1, side_left_tri2,
        side_right_tri1, side_right_tri2
    ))

    # Create the STL mesh
    litho_mesh = mesh.Mesh(np.zeros(all_triangles.shape[0], dtype=mesh.Mesh.dtype))
    litho_mesh.vectors = all_vertices[all_triangles]
    
    return litho_mesh


def main():
    parser = argparse.ArgumentParser(description="Generate a lithophane STL from an image.")
    parser.add_argument("input", nargs="?", default="test1.jpg", help="Input image path")
    parser.add_argument("-o", "--output", default="output.stl", help="Output STL path")
    parser.add_argument("--min-thickness", type=float, default=THICKNESS_SCALE[0], help="Minimum thickness (mm)")
    parser.add_argument("--max-thickness", type=float, default=THICKNESS_SCALE[1], help="Maximum thickness (mm)")
    parser.add_argument("--max-side", type=float, default=MAX_PRINT_SIDE, help="Maximum side length (mm)")

    args = parser.parse_args()

    # Try to find the image in the current directory or the script's directory
    image_path = args.input
    if not os.path.exists(image_path):
        image_path = os.path.join(os.path.dirname(__file__), args.input)

    if not os.path.exists(image_path):
        print(f"Error: Image not found at {args.input} or {image_path}")
        return

    thickness_scale = [args.min_thickness, args.max_thickness]

    print(f"Processing image: {image_path}...")
    img_array = process_image(image_path)
    
    print("Generating mesh...")
    litho_mesh = create_lithophane_mesh(img_array, thickness_scale, args.max_side)
    
    litho_mesh.save(args.output)
    print(f"Successfully saved lithophane to {args.output}")


if __name__ == "__main__":
    main()
