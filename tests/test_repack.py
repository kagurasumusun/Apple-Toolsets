from pathlib import Path
import tempfile
import unittest

from actool_linux.bom import BOMStore
from actool_linux.bomwriter import BOMWriter
from actool_linux.repack import repack


class RepackTests(unittest.TestCase):
    def test_preserves_ids_names_and_payloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "in.car"
            destination = Path(tmp) / "out.car"
            writer = BOMWriter()
            writer.add_block(b"one", "FIRST")
            writer.add_block(b"two")
            writer.add_block(b"three", "THIRD")
            source.write_bytes(writer.build())
            repack(source, destination)
            before = BOMStore.from_path(source)
            after = BOMStore.from_path(destination)
            self.assertEqual(before.variables, after.variables)
            self.assertEqual(before.blocks.keys(), after.blocks.keys())
            for identifier in before.blocks:
                self.assertEqual(bytes(before.block(identifier)), bytes(after.block(identifier)))


if __name__ == "__main__":
    unittest.main()
