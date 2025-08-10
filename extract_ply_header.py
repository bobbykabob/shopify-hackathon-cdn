INPUT_FILE = "chair.ply"
HEADER_OUT = "chair_header.txt"

with open(INPUT_FILE, "rb") as f:
    lines = []
    while True:
        line = f.readline()
        if not line:
            break
        lines.append(line.decode(errors="ignore"))
        if line.strip() == b"end_header":
            break
with open(HEADER_OUT, "w") as out:
    out.writelines(lines)
print(f"Header written to {HEADER_OUT}")
