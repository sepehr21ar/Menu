from __future__ import annotations


DATA_CODEWORDS_L = {1: 19, 2: 34, 3: 55, 4: 80, 5: 108}
ECC_CODEWORDS_L = {1: 7, 2: 10, 3: 15, 4: 20, 5: 26}
ALIGNMENT_CENTERS = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30]}


def make_qr_svg(text: str, box_size: int = 8, border: int = 4) -> str:
    data = text.encode("utf-8")
    version = _choose_version(len(data))
    modules = _build_matrix(version, data)
    size = len(modules)
    full_size = (size + border * 2) * box_size
    rects = []
    for y, row in enumerate(modules):
        for x, is_dark in enumerate(row):
            if is_dark:
                rects.append(
                    f'<rect x="{(x + border) * box_size}" y="{(y + border) * box_size}" '
                    f'width="{box_size}" height="{box_size}"/>'
                )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {full_size} {full_size}" '
        f'width="{full_size}" height="{full_size}" shape-rendering="crispEdges">'
        f'<rect width="100%" height="100%" fill="#fff"/>'
        f'<g fill="#111827">{"".join(rects)}</g></svg>'
    )


def _choose_version(byte_length: int) -> int:
    for version, capacity in DATA_CODEWORDS_L.items():
        if byte_length + 2 <= capacity:
            return version
    raise ValueError("QR text is too long for this built-in generator.")


def _build_matrix(version: int, data: bytes) -> list[list[bool]]:
    size = 21 + 4 * (version - 1)
    modules: list[list[bool | None]] = [[None for _ in range(size)] for _ in range(size)]
    reserved = [[False for _ in range(size)] for _ in range(size)]

    _draw_function_patterns(modules, reserved, version)
    codewords = _encode_codewords(version, data)
    bits = [(codeword >> i) & 1 == 1 for codeword in codewords for i in range(7, -1, -1)]
    _draw_data_bits(modules, reserved, bits)
    _apply_mask(modules, reserved, 0)
    _draw_format_bits(modules, reserved, 0)

    return [[bool(cell) for cell in row] for row in modules]


def _encode_codewords(version: int, data: bytes) -> list[int]:
    capacity = DATA_CODEWORDS_L[version]
    bits = [False, True, False, False]
    bits += [(len(data) >> i) & 1 == 1 for i in range(7, -1, -1)]
    for byte in data:
        bits += [(byte >> i) & 1 == 1 for i in range(7, -1, -1)]
    bits += [False] * min(4, capacity * 8 - len(bits))
    while len(bits) % 8:
        bits.append(False)

    data_codewords = []
    for i in range(0, len(bits), 8):
        value = 0
        for bit in bits[i : i + 8]:
            value = (value << 1) | int(bit)
        data_codewords.append(value)
    pad = 0xEC
    while len(data_codewords) < capacity:
        data_codewords.append(pad)
        pad = 0x11 if pad == 0xEC else 0xEC
    return data_codewords + _reed_solomon_remainder(data_codewords, ECC_CODEWORDS_L[version])


def _draw_function_patterns(
    modules: list[list[bool | None]],
    reserved: list[list[bool]],
    version: int,
) -> None:
    size = len(modules)
    for x, y in ((0, 0), (size - 7, 0), (0, size - 7)):
        _draw_finder(modules, reserved, x, y)

    for i in range(8, size - 8):
        _set_function(modules, reserved, 6, i, i % 2 == 0)
        _set_function(modules, reserved, i, 6, i % 2 == 0)

    for cx in ALIGNMENT_CENTERS[version]:
        for cy in ALIGNMENT_CENTERS[version]:
            if reserved[cy][cx]:
                continue
            _draw_alignment(modules, reserved, cx, cy)

    _set_function(modules, reserved, 8, 4 * version + 9, True)
    for i in range(9):
        if i != 6:
            _reserve(modules, reserved, 8, i)
            _reserve(modules, reserved, i, 8)
    for i in range(8):
        _reserve(modules, reserved, size - 1 - i, 8)
        _reserve(modules, reserved, 8, size - 1 - i)


def _draw_finder(
    modules: list[list[bool | None]],
    reserved: list[list[bool]],
    left: int,
    top: int,
) -> None:
    size = len(modules)
    for y in range(top - 1, top + 8):
        for x in range(left - 1, left + 8):
            if 0 <= x < size and 0 <= y < size:
                reserved[y][x] = True
                modules[y][x] = False
    for y in range(7):
        for x in range(7):
            dark = x in (0, 6) or y in (0, 6) or (2 <= x <= 4 and 2 <= y <= 4)
            _set_function(modules, reserved, left + x, top + y, dark)


def _draw_alignment(
    modules: list[list[bool | None]],
    reserved: list[list[bool]],
    cx: int,
    cy: int,
) -> None:
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            dark = max(abs(dx), abs(dy)) != 1
            _set_function(modules, reserved, cx + dx, cy + dy, dark)


def _draw_data_bits(
    modules: list[list[bool | None]],
    reserved: list[list[bool]],
    bits: list[bool],
) -> None:
    size = len(modules)
    bit_index = 0
    upward = True
    x = size - 1
    while x > 0:
        if x == 6:
            x -= 1
        for y_offset in range(size):
            y = size - 1 - y_offset if upward else y_offset
            for col in (x, x - 1):
                if not reserved[y][col]:
                    modules[y][col] = bits[bit_index] if bit_index < len(bits) else False
                    bit_index += 1
        upward = not upward
        x -= 2


def _apply_mask(
    modules: list[list[bool | None]],
    reserved: list[list[bool]],
    mask: int,
) -> None:
    for y, row in enumerate(modules):
        for x, value in enumerate(row):
            if reserved[y][x]:
                continue
            if _mask_condition(mask, x, y):
                modules[y][x] = not bool(value)


def _mask_condition(mask: int, x: int, y: int) -> bool:
    if mask == 0:
        return (x + y) % 2 == 0
    raise ValueError("Unsupported mask")


def _draw_format_bits(
    modules: list[list[bool | None]],
    reserved: list[list[bool]],
    mask: int,
) -> None:
    size = len(modules)
    data = (0b01 << 3) | mask
    rem = data << 10
    for i in range(14, 9, -1):
        if (rem >> i) & 1:
            rem ^= 0x537 << (i - 10)
    bits = ((data << 10) | rem) ^ 0x5412

    for i in range(15):
        bit = (bits >> i) & 1 == 1
        if i < 6:
            _set_function(modules, reserved, 8, i, bit)
        elif i == 6:
            _set_function(modules, reserved, 8, 7, bit)
        elif i == 7:
            _set_function(modules, reserved, 8, 8, bit)
        elif i == 8:
            _set_function(modules, reserved, 7, 8, bit)
        else:
            _set_function(modules, reserved, 14 - i, 8, bit)

        if i < 8:
            _set_function(modules, reserved, size - 1 - i, 8, bit)
        else:
            _set_function(modules, reserved, 8, size - 15 + i, bit)


def _set_function(
    modules: list[list[bool | None]],
    reserved: list[list[bool]],
    x: int,
    y: int,
    dark: bool,
) -> None:
    modules[y][x] = dark
    reserved[y][x] = True


def _reserve(
    modules: list[list[bool | None]],
    reserved: list[list[bool]],
    x: int,
    y: int,
) -> None:
    reserved[y][x] = True
    if modules[y][x] is None:
        modules[y][x] = False


def _reed_solomon_remainder(data: list[int], degree: int) -> list[int]:
    generator = _reed_solomon_generator(degree)
    result = [0] * degree
    for byte in data:
        factor = byte ^ result.pop(0)
        result.append(0)
        for i, coefficient in enumerate(generator):
            result[i] ^= _gf_multiply(coefficient, factor)
    return result


def _reed_solomon_generator(degree: int) -> list[int]:
    result = [1]
    root = 1
    for _ in range(degree):
        result.append(0)
        for i in range(len(result) - 1):
            result[i] = _gf_multiply(result[i], root)
            result[i] ^= result[i + 1]
        root = _gf_multiply(root, 0x02)
    return result[:-1]


def _gf_multiply(x: int, y: int) -> int:
    result = 0
    while y:
        if y & 1:
            result ^= x
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
        y >>= 1
    return result
