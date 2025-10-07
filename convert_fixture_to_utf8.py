import io
import sys
from pathlib import Path

COMMON_ENCODINGS = ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be")


def convert_file(src: str) -> int:
    """Read `src` trying common encodings and write a UTF-8 copy with suffix `.utf8.json`.

    Returns 0 on success, 2 on read failure.
    """
    src_path = Path(src)
    if not src_path.exists():
        print(f"Source not found: {src}")
        return 2

    text = None
    used_enc = None
    for enc in COMMON_ENCODINGS:
        try:
            with io.open(src_path, "r", encoding=enc) as f:
                text = f.read()
            used_enc = enc
            print(f"Read {src} using encoding: {enc}")
            break
        except Exception:
            continue

    if text is None:
        print(f"Failed to read the fixture {src} with common encodings; please check the file.")
        return 2

    dst = src_path.with_name(src_path.stem + ".utf8.json")
    with io.open(dst, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Wrote UTF-8 fixture to {dst} (original encoding guessed: {used_enc})")
    return 0


def main(argv=None):
    argv = list(argv or sys.argv[1:])
    if not argv:
        print("Usage: convert_fixture_to_utf8.py <fixture.json> [more fixtures...]")
        return 2

    exit_codes = []
    for src in argv:
        rc = convert_file(src)
        exit_codes.append(rc)

    return 0 if all(c == 0 for c in exit_codes) else 2


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
