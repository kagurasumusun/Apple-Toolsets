import os
import unittest

from actool_linux.bom import BOMStore
from actool_linux.car import CARFile


# The real-app fixture (`fixtures/firefox-Assets.car`) was removed for license
# hygiene on 2026-07-17. Its role is replaced by
# `fixtures/selfgen-rich-Assets.car`, compiled by Apple actool in CI from this
# project's own inputs (see fixtures/README.md). Skip until the self-made
# fixture is present locally, then pin the observed registry values.
RICH_FIXTURE = 'fixtures/selfgen-rich-Assets.car'


@unittest.skipUnless(os.path.exists(RICH_FIXTURE), 'self-made rich fixture is not generated yet')
class CARAppearanceRegistryTests(unittest.TestCase):
    def test_selfgen_rich_appearance_registry(self):
        car = CARFile(BOMStore.from_path(RICH_FIXTURE))
        registry = {entry.name: entry.value for entry in car.appearances}
        # Pinned values measured from the CI-generated fixture; update together
        # with tools/make_public_fixtures.py when inputs change.
        self.assertIn('NSAppearanceNameAqua', registry)
        self.assertIn('NSAppearanceNameDarkAqua', registry)

    def test_brandassets_target_tv_appearance_registry(self):
        car = CARFile(BOMStore.from_path('fixtures/brandassets-target-tv-Assets.car'))
        registry = {entry.name: entry.value for entry in car.appearances}
        self.assertEqual(registry, {'UIAppearanceAny': 0})


if __name__ == '__main__':
    unittest.main()
