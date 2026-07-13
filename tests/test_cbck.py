import struct
import unittest

import lzfse

from actool_linux.bom import BOMError
from actool_linux.cbck import parse_cbck


class CBCKTests(unittest.TestCase):
    def test_parses_and_decompresses_chunks(self):
        sources = [b"abcd" * 10, b"efgh" * 3]
        chunks = []
        for rows, source in zip((5, 2), sources):
            compressed = lzfse.compress(source)
            chunks.append(b"KCBC" + struct.pack("<4I", 0, 0, rows, len(compressed)) + compressed)
        parsed = parse_cbck(b"MLEC" + struct.pack("<3I", 3, 4, 2) + b"".join(chunks))
        self.assertEqual([item.row_count for item in parsed.chunks], [5, 2])
        self.assertEqual(parsed.decompress(), b"".join(sources))

    def test_rejects_truncated_chunk(self):
        raw = b"MLEC" + struct.pack("<3I", 3, 4, 1) + b"KCBC" + struct.pack("<4I", 0, 0, 1, 100) + b"short"
        with self.assertRaisesRegex(BOMError, "truncated"):
            parse_cbck(raw)

    def test_rejects_trailing_bytes(self):
        compressed = lzfse.compress(b"pixel")
        raw = b"MLEC" + struct.pack("<3I", 3, 4, 1) + b"KCBC" + struct.pack("<4I", 0, 0, 1, len(compressed)) + compressed + b"x"
        with self.assertRaisesRegex(BOMError, "trailing"):
            parse_cbck(raw)


if __name__ == "__main__":
    unittest.main()
