# Lithophane STL Generator

This project generates 3D-printable lithophane STL files from input images.

## Project Structure

- `src/main.py`: Main entry point and core logic.
- `src/requirements.txt`: Python dependencies.

## Development Setup

### Dependencies
Install dependencies using pip:
```bash
pip install -r src/requirements.txt
```

### Running the Script
Run the script with an input image:
```bash
python src/main.py <input_image> -o <output_stl>
```
Example:
```bash
python src/main.py test1.jpg -o output.stl
```

## Core Logic & Conventions

### Image Processing
- Preprocessing is done in `process_image`.
- Images are converted to grayscale and inverted (darker parts become thicker).
- Contrast and Gaussian blur are applied to improve print quality.

### Mesh Generation
- Logic is in `create_lithophane_mesh`.
- Uses `numpy` for vectorized vertex and triangle generation.
- Top surface height is mapped from image intensity.
- Bottom surface is flat ($Z=0$).
- Side walls are generated to close the mesh.

### Vectorization
- Avoid loops for mesh generation; use `numpy` indexing and slicing.
- The `numpy-stl` library is used to save the final mesh.

## AI Agent Guidelines

- **Performance**: When modifying mesh generation, prioritize vectorized `numpy` operations.
- **Dependencies**: Use `requirements.txt` for any new dependencies.
- **CLI**: Use `argparse` for new command-line options.
- **Math**: Mesh generation involves coordinate mapping and triangle orientation. Ensure triangles follow the right-hand rule for normals if adding new surfaces.
