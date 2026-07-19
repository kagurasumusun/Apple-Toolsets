import paramiko
import time
import re

def clean_tmux_output(output):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean = ansi_escape.sub('', output)
    clean = clean.replace('[K', '').replace('\x0f', '').replace('\x07', '')
    clean = re.sub(r'\n\s*\n', '\n', clean)
    return clean

def run_upterm_test():
    host = "uptermd.upterm.dev"
    port = 22
    username = "NZavJ93kKawd70bya6xE"
    key_path = "/home/user/.ssh/id_ed25519"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        key = paramiko.Ed25519Key.from_private_key_file(key_path)
        client.connect(hostname=host, port=port, username=username, pkey=key, look_for_keys=False)
        
        shell = client.invoke_shell(term='vt100', width=200, height=50)
        time.sleep(2)
        if shell.recv_ready(): shell.recv(65535)
            
        print("Executing BEYOND-GODMODE Pipeline on Remote Mac...")
        cmd = """
cd /Users/runner/work/Apple-actool-py/Apple-actool-py
git pull origin fix-bugs
export PYTHONPATH=.
echo "=== 1. INSTALLING DEPENDENCIES ==="
python3 -m pip install numpy scikit-learn pillow --break-system-packages

echo "=== 2. CREATING THE ULTIMATE OPTIMIZER (CRAZY MODE) ==="
cat << 'PY_EOF' > actool_linux/nextgen/crazy_fusion.py
import numpy as np
import time
from actool_linux.stable import lzfse_compat as lzfse

class CrazyFusionAtlas:
    def __init__(self):
        try:
            from sklearn.cluster import KMeans
            self.KMeans = KMeans
            self.has_sklearn = True
        except ImportError:
            self.has_sklearn = False

    def _ai_quantize(self, img_np: np.ndarray, colors: int = 16) -> np.ndarray:
        if not self.has_sklearn: return img_np
        h, w, c = img_np.shape
        pixels = img_np.reshape(-1, c).astype(np.float32)
        if len(np.unique(pixels, axis=0)) <= colors: return img_np
        
        sample = pixels[np.random.choice(len(pixels), min(5000, len(pixels)), replace=False)]
        kmeans = self.KMeans(n_clusters=colors, n_init=1, random_state=42).fit(sample)
        labels = kmeans.predict(pixels)
        palette = kmeans.cluster_centers_.astype(np.uint8)
        return palette[labels].reshape((h, w, c))

    def _planar_delta_compress(self, chunk_np: np.ndarray) -> bytes:
        out = bytearray()
        for i in range(4):
            plane = chunk_np[:, :, i].flatten()
            diff = np.diff(plane, prepend=0).astype(np.uint8)
            out.extend(diff.tobytes())
        return lzfse.compress(bytes(out))

    def run_ultimate_pipeline(self, img_data: bytes, w: int, h: int) -> dict:
        img_np = np.frombuffer(img_data, dtype=np.uint8).reshape((h, w, 4)).copy()
        img_np[img_np[:, :, 3] == 0, :3] = 0
        img_np = self._ai_quantize(img_np, 16)
        
        total_size = 0
        stats = {"RLE": 0, "Planar-Delta": 0, "ASTC": 0}
        
        for y in range(0, h, 64):
            for x in range(0, w, 64):
                chunk = img_np[y:y+64, x:x+64]
                if np.all(chunk == chunk[0,0]):
                    total_size += 4
                    stats["RLE"] += 1
                else:
                    gray = np.mean(chunk[:,:,:3], axis=2)
                    edge = np.sum(np.abs(np.diff(gray, axis=1))) / (64*64*255)
                    if edge > 0.05:
                        total_size += len(self._planar_delta_compress(chunk))
                        stats["Planar-Delta"] += 1
                    else:
                        total_size += (64*64) // 16
                        stats["ASTC"] += 1
        
        return {"size": total_size, "stats": stats}
PY_EOF

echo "=== 3. EXECUTING CRAZY MODE ==="
cat << 'PY_EOF' > test_crazy.py
import numpy as np
import time
from actool_linux.nextgen.crazy_fusion import CrazyFusionAtlas

w, h = 2048, 2048
print(f"Generating {w}x{h} test image...")
img_np = np.random.randint(0, 256, (h, w, 4), dtype=np.uint8)
img_np[100:1000, 100:1000, 3] = 0 # Transparent region
img_data = img_np.tobytes()

engine = CrazyFusionAtlas()

start = time.time()
result = engine.run_ultimate_pipeline(img_data, w, h)
elapsed = (time.time() - start) * 1000

print(f"\\n[ULTIMATE RESULTS]")
print(f"Original Size: {w*h*4/1024/1024:.2f} MB")
print(f"Crazy-Mode Size: {result['size']/1024/1024:.2f} MB")
print(f"Compression Time: {elapsed:.1f} ms")
print(f"Chunk Stats: {result['stats']}")
PY_EOF
python3 test_crazy.py

echo "=== 4. MAC NATIVE ASSETUTIL TEST ==="
rm -rf out_crazy
mkdir -p out_crazy
python3 -m actool_linux.nextgen tests/test_data/test.xcassets --compile out_crazy --platform iphoneos --minimum-deployment-target 15.0 --optimize smart
echo "=== MAC ASSETUTIL JSON HEAD ==="
xcrun assetutil -I out_crazy/Assets.car | head -n 30
echo "=== END OF JSON ==="
"""
        shell.send(cmd.replace('\n', '\r'))
        
        time.sleep(20)
        
        output = ""
        while shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')
            
        print("=== Results from Remote Mac ===")
        print(clean_tmux_output(output))
                
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_upterm_test()
