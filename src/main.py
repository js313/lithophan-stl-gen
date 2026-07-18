from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import numpy as np
from stl import mesh

THICKNESS_SCALE = [0.6, 3.0]
MAX_PRINT_SIDE = 150
CONTRAST = 1.2

# Load Image
with Image.open(
    "/Users/jeenitsharma/Documents/Code/Personal/lithophane-stl-gen/src/test1.jpg"
) as original_image:
    # Convert the image to grayscale
    enhancer = ImageEnhance.Contrast(original_image)
    contrast_image = enhancer.enhance(CONTRAST)
    blurred_image = contrast_image.filter(ImageFilter.GaussianBlur(radius=1))

    gray_scale_image = blurred_image.convert("L")
    inverted_image = ImageOps.invert(gray_scale_image)

    # Invert image so light parts caome out thinner on lithophane
    inverted_image_array = np.asarray(inverted_image)
    img_len = len(inverted_image_array)
    img_bth = len(inverted_image_array[0])
    img_pix_cnt = img_len * img_bth

    brightest_pix_val = 0
    dullest_pix_val = 255
    for row in inverted_image_array:
        for pix in row:
            if pix > brightest_pix_val:
                brightest_pix_val = pix
            if pix < dullest_pix_val:
                dullest_pix_val = pix

    print(brightest_pix_val, dullest_pix_val)

    # Get z-axis of each pixel
    height_map_array = np.zeros((img_len, img_bth))
    i = 0
    for row in inverted_image_array:
        j = 0
        for pix in row:
            height_map_array[i][j] = (
                THICKNESS_SCALE[0]
                + (
                    (THICKNESS_SCALE[1] - THICKNESS_SCALE[0])
                    / (brightest_pix_val - dullest_pix_val)
                )
                * pix
            )
            j += 1
        i += 1

    # Create STL file from height map array
    # Top
    scaling_factor = MAX_PRINT_SIDE / max(img_len, img_bth)

    top_vertices = np.zeros((img_len * img_bth, 3))
    for i in range(img_len):
        for j in range(img_bth):
            idx = img_bth * i + j
            top_vertices[idx][0] = i * scaling_factor
            top_vertices[idx][1] = j * scaling_factor
            top_vertices[idx][2] = height_map_array[i][j]

    bottom_vertices = np.zeros((img_len * img_bth, 3))
    for i in range(img_len):
        for j in range(img_bth):
            idx = img_bth * i + j
            bottom_vertices[idx][0] = i * scaling_factor
            bottom_vertices[idx][1] = j * scaling_factor
            bottom_vertices[idx][2] = 0

    all_vertices = np.vstack((top_vertices, bottom_vertices))

    print("all_vertices", all_vertices)

    top_triangles = np.zeros(((img_len - 1) * (img_bth - 1) * 2, 3), dtype=int)
    t = 0
    for i in range(img_len - 1):
        for j in range(img_bth - 1):
            top_left = i * img_bth + j
            top_right = top_left + 1
            bottom_left = top_left + img_bth
            bottom_right = bottom_left + 1

            top_triangles[t] = [top_left, bottom_left, top_right]
            top_triangles[t + 1] = [top_right, bottom_left, bottom_right]
            t += 2

    print("top_triangles", top_triangles)

    # Bottom
    bottom_triangles = np.zeros(((img_len - 1) * (img_bth - 1) * 2, 3), dtype=int)
    t = 0
    for i in range(img_len - 1):
        for j in range(img_bth - 1):
            top_left = i * img_bth + j + img_pix_cnt
            top_right = top_left + 1
            bottom_left = top_left + img_bth
            bottom_right = bottom_left + 1

            bottom_triangles[t] = [top_left, top_right, bottom_left]
            bottom_triangles[t + 1] = [top_right, bottom_right, bottom_left]
            t += 2

    print("bottom_triangles", bottom_triangles)

    # Sides
    # Up
    side_up_triangles = np.zeros(((img_bth - 1) * 2, 3), dtype=int)  # problematic
    t = 0
    for i in range(img_bth - 1):
        top_left = i
        top_right = i + 1
        bottom_left = i + img_pix_cnt
        bottom_right = bottom_left + 1

        side_up_triangles[t] = [top_left, top_right, bottom_left]
        side_up_triangles[t + 1] = [top_right, bottom_right, bottom_left]
        t += 2
    print("side_up_triangles", side_up_triangles)

    # Bottom
    side_bottom_triangles = np.zeros(((img_bth - 1) * 2, 3), dtype=int)
    t = 0
    for i in range(img_pix_cnt - img_bth, img_pix_cnt - 1):
        top_left = i
        top_right = i + 1
        bottom_left = i + img_pix_cnt
        bottom_right = bottom_left + 1

        side_bottom_triangles[t] = [top_left, bottom_left, top_right]
        side_bottom_triangles[t + 1] = [top_right, bottom_left, bottom_right]
        t += 2
    print("side_bottom_triangles", side_bottom_triangles)

    # Left
    side_left_triangles = np.zeros(((img_len - 1) * 2, 3), dtype=int)
    t = 0
    for i in range(0, img_pix_cnt - img_bth - 1, img_bth):
        top_left = i
        top_right = i + img_bth
        bottom_left = i + img_pix_cnt
        bottom_right = bottom_left + img_bth

        side_left_triangles[t] = [top_left, bottom_left, top_right]
        side_left_triangles[t + 1] = [top_right, bottom_left, bottom_right]
        t += 2
    print("side_left_triangles", side_left_triangles)

    # Right
    side_right_triangles = np.zeros(((img_len - 1) * 2, 3), dtype=int)  # Problematic
    t = 0
    for i in range(img_bth - 1, img_pix_cnt - 1, img_bth):
        top_left = i
        top_right = i + img_bth
        bottom_left = i + img_pix_cnt
        bottom_right = bottom_left + img_bth

        side_right_triangles[t] = [top_left, top_right, bottom_left]
        side_right_triangles[t + 1] = [top_right, bottom_right, bottom_left]
        t += 2
    print("side_right_triangles", side_right_triangles)

    all_triangles = np.concatenate(
        [
            top_triangles,
            bottom_triangles,
            side_up_triangles,
            side_bottom_triangles,
            side_left_triangles,
            side_right_triangles,
        ]
    )
    final_mesh = mesh.Mesh(np.zeros(all_triangles.shape[0], dtype=mesh.Mesh.dtype))
    final_mesh.vectors = all_vertices[all_triangles]

    # Save mesh to stl file
    final_mesh.save("output.stl")
