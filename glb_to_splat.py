import trimesh
import numpy as np
from io import BytesIO
import argparse

# This script will convert a .glb file to a .splat file by extracting vertex positions and colors.
# Note: .splat format here is assumed to be similar to the one used in ply_to_splat.py, but with only position and color (no scale, rotation, or SH coefficients).

def process_glb_to_splat(glb_file_path):
    import random
    debug_samples = []
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
    for idx, f_idx in enumerate(sampled_faces):
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
        if idx < 10:
            debug_samples.append({'face': f_idx, 'v_idx': v_idx.tolist(), 'pos': pos.tolist(), 'bary': [b0, b1, b2], 'uv': uv_sample.tolist() if uv is not None else None})
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
            if i < 10:
                debug_samples[i]['color'] = colors[i].tolist()
    buffer = BytesIO()
    SH_C0 = 0.28209479177387814
    default_scale = np.array([0.0, 0.0, 0.0], dtype=np.float32)  # log(1) = 0
    default_rot = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)  # identity quaternion
    default_opacity = 1.0
    for i, (pos, color) in enumerate(zip(sampled_points, colors)):
        # Position (3 floats)
        buffer.write(pos.astype(np.float32).tobytes())
        # Scale (3 floats, log scale as in ply_to_splat.py)
        buffer.write(default_scale.tobytes())
        # Color (4 uint8: RGB from texture, A from opacity)
        rgba = np.array([
            color[0],
            color[1],
            color[2],
            int(255 * default_opacity)
        ], dtype=np.uint8)
        buffer.write(rgba.tobytes())
        # Rotation (4 uint8: normalized quaternion mapped to [0,255])
        rot = default_rot / np.linalg.norm(default_rot)
        rot_bytes = ((rot * 128) + 128).clip(0, 255).astype(np.uint8)
        buffer.write(rot_bytes.tobytes())
        if i < 10:
            debug_samples[i]['rgba'] = rgba.tolist()
            debug_samples[i]['rot_bytes'] = rot_bytes.tolist()
    print("DEBUG SAMPLES (first 10):")
    for sample in debug_samples:
        print(sample)
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
