import struct
import sys

INPUT_FILE = "chair.ply"
OUTPUT_FILE = "chair_no_white.ply"
WHITE_THRESHOLD = 240  # RGB values above this are considered close to white

def read_ply_header(f):
    header = []
    while True:
        line = f.readline().decode()
        header.append(line)
        if line.strip() == "end_header":
            break
    return header

def parse_vertex_count(header):
    for line in header:
        if line.startswith("element vertex"):
            return int(line.split()[2])
    raise ValueError("No vertex count found in header")

def parse_vertex_format(header):
    props = []
    for line in header:
        if line.startswith("property"):
            props.append(line.split()[2])
        if line.startswith("element face"):
            break
    return props

def main():

    with open(INPUT_FILE, "rb") as f:
        header = read_ply_header(f)
        vertex_count = parse_vertex_count(header)
        # Each vertex has 16 float properties
        vertex_fmt = "16f"
        vertex_size = struct.calcsize(vertex_fmt)
        vertices = []
        for _ in range(vertex_count):
            data = f.read(vertex_size)
            if len(data) < vertex_size:
                break
            vertex = struct.unpack(vertex_fmt, data)
            f_dc_0, f_dc_1, f_dc_2 = vertex[6], vertex[7], vertex[8]
            if f_dc_0 > 0.94 and f_dc_1 > 0.94 and f_dc_2 > 0.94:
                continue
            vertices.append(data)
        rest = f.read()
    # Update header vertex count
    new_header = []
    for line in header:
        if line.startswith("element vertex"):
            new_header.append(f"element vertex {len(vertices)}\n")
        else:
            new_header.append(line)
    with open(OUTPUT_FILE, "wb") as f:
        f.write("".join(new_header).encode())
        for v in vertices:
            f.write(v)
        f.write(rest)
    print(f"Filtered file written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
