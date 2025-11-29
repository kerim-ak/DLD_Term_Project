import sys

OPCODES = {
    "ADD":   0b00000,
    "SUB":   0b00001,
    "NAND":  0b00010,
    "NOR":   0b00011,
    "SRL":   0b00100,
    "SRA":   0b00101,
    "ADDI":  0b00110,
    "SUBI":  0b00111,
    "NANDI": 0b01000,
    "NORI":  0b01001,
    "LD":    0b01010,
    "ST":    0b01011,
    "JUMP":  0b01100,
    "JAL":   0b01101,
    "LUI":   0b01110,
    "CMOV":  0b01111,
    "PUSH":  0b10000,
    "POP":   0b10001,
}

def reg_number(r):
    """Convert R0..R15 to int."""
    if not r.startswith("R"):
        raise ValueError(f"Invalid register: {r}")
    num = int(r[1:])
    if not 0 <= num <= 15:
        raise ValueError(f"Register out of range: {r}")
    return num

def signed(val, bits):
    """Convert integer into signed 'bits'-bit two’s complement."""
    if val < 0:
        val = (1 << bits) + val
    return val & ((1 << bits) - 1)

def encode_R(op, rd, rs1, rs2):
    """R-type: opcode(5) | rd(4) | rs1(4) | rs2(4) | 0(1)."""
    return (
        (op << 13) |
        (rd << 9) |
        (rs1 << 5) |
        (rs2 << 1)
    )

def encode_I(op, rd, rs1, imm5):
    """I-type: opcode(5) | rd(4) | rs1(4) | imm5(5)."""
    imm5 = signed(imm5, 5)
    return (
        (op << 13) |
        (rd << 9) |
        (rs1 << 5) |
        imm5
    )

def encode_M(op, reg, addr):
    """M-type: opcode(5) | reg(4) | addr(9)."""
    addr &= 0x1FF  # 9 bits
    return (
        (op << 13) |
        (reg << 9) |
        addr
    )

def encode_J(op, offset):
    """J-type: opcode(5) | offset13."""
    offset = signed(offset, 13)
    return (
        (op << 13) |
        offset
    )

def encode_U(op, rd, imm9):
    """U-type: opcode(5) | rd(4) | imm9."""
    imm9 &= 0x1FF
    return (
        (op << 13) |
        (rd << 9) |
        imm9
    )

def encode_CMOV(op, r1, r2, r3):
    """C-type: opcode | r1 | r2 | r3 | 0."""
    return (
        (op << 13) |
        (r1 << 9) |
        (r2 << 5) |
        (r3 << 1)
    )

def encode_STACK(op, reg):
    """S-type: opcode | reg | zero padding."""
    return (op << 13) | (reg << 9)

def parse_line(line):
    line = line.split("//")[0].strip()  # remove comments
    if line == "":
        return None

    parts = line.replace(",", " ").split()
    ins = parts[0].upper()

    if ins not in OPCODES:
        raise ValueError(f"Unknown instruction: {ins}")

    op = OPCODES[ins]

    # R-type instructions
    if ins in ["ADD", "SUB", "NAND", "NOR", "SRL", "SRA"]:
        rd = reg_number(parts[1])
        rs1 = reg_number(parts[2])
        rs2 = reg_number(parts[3])
        return encode_R(op, rd, rs1, rs2)

    # I-type
    if ins in ["ADDI", "SUBI", "NANDI", "NORI"]:
        rd = reg_number(parts[1])
        rs1 = reg_number(parts[2])
        imm5 = int(parts[3])
        return encode_I(op, rd, rs1, imm5)

    # LD
    if ins == "LD":
        rd = reg_number(parts[1])
        addr = int(parts[2])
        return encode_M(op, rd, addr)

    # ST
    if ins == "ST":
        rs = reg_number(parts[1])
        addr = int(parts[2])
        return encode_M(op, rs, addr)

    # JUMP, JAL
    if ins in ["JUMP", "JAL"]:
        offset = int(parts[1])
        return encode_J(op, offset)

    # LUI
    if ins == "LUI":
        rd = reg_number(parts[1])
        imm9 = int(parts[2])
        return encode_U(op, rd, imm9)

    # CMOV
    if ins == "CMOV":
        r1 = reg_number(parts[1])
        r2 = reg_number(parts[2])
        r3 = reg_number(parts[3])
        return encode_CMOV(op, r1, r2, r3)

    # PUSH, POP
    if ins in ["PUSH", "POP"]:
        reg = reg_number(parts[1])
        return encode_STACK(op, reg)

    raise ValueError(f"Unhandled instruction format: {ins}")

def assemble_file(input_file, output_file):
    machine_codes = []

    with open(input_file, "r") as f:
        for line in f:
            try:
                encoded = parse_line(line)
                if encoded is not None:
                    machine_codes.append(encoded)
            except Exception as e:
                print(f"Error in line: {line.strip()}")
                raise

    # Write output
    with open(output_file, "w") as f:
        f.write("v2.0 raw\n")

        hex_words = [f"{code:05x}" for code in machine_codes]

        # Write 8 per line (optional, nicer for Logisim)
        for i in range(0, len(hex_words), 8):
            f.write(" ".join(hex_words[i:i+8]) + "\n")

    print(f"Assembly complete. Output written to {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 assembler.py input.asm output.hex")
        sys.exit(1)

    assemble_file(sys.argv[1], sys.argv[2])
