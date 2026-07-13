from PIL import Image, ImageOps
import numpy as np
from stl import mesh

THICKNESS_SCALE = [0.8, 3.2]

# Load Image
with Image.open(
    "/Users/jeenitsharma/Documents/Code/Personal/lithophane-stl-gen/src/test1.jpg"
) as original_image:
    # Convert the image to grayscale
    gray_scale_image = original_image.convert("L")
    inverted_image = ImageOps.invert(gray_scale_image)

    # Invert image so light parts caome out thinner on lithophane
    inverted_image_array = np.asarray(inverted_image)
    img_len = len(inverted_image_array)
    img_bth = len(inverted_image_array[0])

    # Get z-axis of each pixel
    height_map_array = np.zeros((img_len, img_bth))
    i = 0
    for row in inverted_image_array:
        j = 0
        for pix in row:
            height_map_array[i][j] = (
                THICKNESS_SCALE[0]
                + ((THICKNESS_SCALE[1] - THICKNESS_SCALE[0]) / (255 - 0)) * pix
            )
            j += 1
        i += 1

    print(height_map_array)

    # Image.fromarray(height_map_array * 10).show()

    # Create STL file from height map array
    vertices = np.zeros((img_len * img_bth, 3))
    for i in range(img_len):
        for j in range(img_bth):
            idx = img_bth * i + j
            vertices[idx][0] = i
            vertices[idx][1] = j
            vertices[idx][2] = height_map_array[i][j]

    print(vertices)

    stl_triangles = np.zeros(((img_len - 1) * (img_bth - 1) * 2, 3), dtype=int)
    t = 0
    for i in range(img_len - 1):
        for j in range(img_bth - 1):
            top_left = i * img_bth + j
            top_right = top_left + 1
            bottom_left = top_left + img_bth
            bottom_right = bottom_left + 1

            stl_triangles[t] = [top_left, top_right, bottom_left]
            stl_triangles[t + 1] = [top_right, bottom_left, bottom_right]
            t += 2

    print(stl_triangles)

    final_mesh = mesh.Mesh(np.zeros(stl_triangles.shape[0], dtype=mesh.Mesh.dtype))

    final_mesh.vectors = vertices[stl_triangles]

    # Save mesh to stl file
    final_mesh.save("output.stl")
