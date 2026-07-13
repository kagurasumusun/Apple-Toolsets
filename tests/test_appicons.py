import unittest
from actool_linux.appicons import app_icon_sidecar_specs

class AppIconSidecarTests(unittest.TestCase):
 def test_ios_compatibility_manifest(self):
  x=app_icon_sidecar_specs('iphoneos'); self.assertEqual(len(x),13)
  self.assertIn(('AppIcon60x60@3x.png',180,180),x)
  self.assertIn(('AppIcon83.5x83.5@2x~ipad.png',167,167),x)
 def test_watch_and_mac_manifests(self):
  self.assertEqual(len(app_icon_sidecar_specs('watchos')),9)
  self.assertEqual(len(app_icon_sidecar_specs('macosx')),10)
 def test_layered_platforms_have_no_flattened_sidecar(self):
  self.assertEqual(app_icon_sidecar_specs('appletvos'),())
  self.assertEqual(app_icon_sidecar_specs('xros'),())

if __name__=='__main__': unittest.main()
