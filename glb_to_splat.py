import trimesh
import numpy as np
from io import BytesIO
import argparse

# This script will convert a .glb file to a .splat file by extracting vertex positions and colors.
# Note: .splat format here is assumed to be similar to the one used in ply_to_splat.py, but with only position and color (no scale, rotation, or SH coefficients).

def process_glb_to_splat(glb_file_path):
    import PIL.Image
    scene = trimesh.load(glb_file_path)
    if hasattr(scene, 'geometry'):
        mesh = list(scene.geometry.values())[0]
    else:
        mesh = scene
    # Uniformly sample points on the mesh surface
    num_samples = 10000  # Default, can be parameterized
    faces = mesh.faces
    vertices = mesh.vertices
    face_areas = mesh.area_faces
    face_probs = face_areas / face_areas.sum()
    sampled_faces = np.random.choice(len(faces), size=num_samples, p=face_probs)
    sampled_points = []
    sampled_uvs = []
    if hasattr(mesh.visual, 'uv') and mesh.visual.uv is not None:
        uv = mesh.visual.uv
    else:
        uv = None
    for f_idx in sampled_faces:
        v_idx = faces[f_idx]
        # Barycentric coordinates
        r1 = np.random.rand()
        r2 = np.random.rand()
        sqrt_r1 = np.sqrt(r1)
        b0 = 1 - sqrt_r1
        b1 = sqrt_r1 * (1 - r2)
        b2 = sqrt_r1 * r2
        pos = b0 * vertices[v_idx[0]] + b1 * vertices[v_idx[1]] + b2 * vertices[v_idx[2]]
        sampled_points.append(pos)
        if uv is not None:
            uv0, uv1, uv2 = uv[v_idx[0]], uv[v_idx[1]], uv[v_idx[2]]
            uv_sample = b0 * uv0 + b1 * uv1 + b2 * uv2
            sampled_uvs.append(uv_sample)
    sampled_points = np.array(sampled_points, dtype=np.float32)
    colors = np.full((num_samples, 3), 255, dtype=np.uint8)
    if uv is not None and hasattr(mesh.visual, 'material') and hasattr(mesh.visual.material, 'baseColorTexture') and mesh.visual.material.baseColorTexture is not None:
        img = mesh.visual.material.baseColorTexture
        img = img.convert('RGB')
        w, h = img.size
        for i, uv_coord in enumerate(sampled_uvs):
            x = int(uv_coord[0] * w)
            y = int((1 - uv_coord[1]) * h)
            x = np.clip(x, 0, w - 1)
            y = np.clip(y, 0, h - 1)
            colors[i] = img.getpixel((x, y))
    buffer = BytesIO()
    for pos, color in zip(sampled_points, colors):
        buffer.write(pos.tobytes())
        buffer.write(color.astype(np.uint8).tobytes())
    return buffer.getvalue()

def save_splat_file(splat_data, output_path):
    with open(output_path, "wb") as f:
        f.write(splat_data)

def main():
    parser = argparse.ArgumentParser(description="Convert GLB files to SPLAT format.")
    parser.add_argument("input_files", nargs="+", help="The input GLB files to process.")
    parser.add_argument("--output", "-o", default="output.splat", help="The output SPLAT file.")
    args = parser.parse_args()
    for input_file in args.input_files:
        print(f"Processing {input_file}...")
        splat_data = process_glb_to_splat(input_file)
        output_file = args.output if len(args.input_files) == 1 else input_file + ".splat"
        save_splat_file(splat_data, output_file)
        print(f"Saved {output_file}")

if __name__ == "__main__":
    main()
