import numpy as np
import time
import os
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    import onnx
    import onnxruntime as ort
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# ==========================================
# 1. PyTorch Model Definition
# ==========================================
class CompressionOptimizerCNN(nn.Module):
    def __init__(self):
        super().__init__()
        # Input: (Batch, 4, 64, 64) -> RGBA image chunk
        self.features = nn.Sequential(
            nn.Conv2d(4, 16, kernel_size=3, stride=2, padding=1), # 32x32
            nn.ReLU(),
            nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1), # 16x16
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1), # 8x8
            nn.ReLU(),
            nn.Flatten()
        )
        self.classifier = nn.Sequential(
            nn.Linear(64 * 8 * 8, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 4) # 4 classes: 0=RLE, 1=LZFSE, 2=ASTC_8x8, 3=Raw
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

def create_dummy_dataset(num_samples=1000):
    """
    Simulate a dataset of image chunks and their 'optimal' compression strategy.
    In reality, we would extract 64x64 chunks from thousands of iOS apps and
    benchmark them through all algorithms to get the true labels.
    """
    print("Generating simulated training data...")
    X = np.random.rand(num_samples, 4, 64, 64).astype(np.float32)
    y = np.random.randint(0, 4, size=(num_samples,))
    return torch.tensor(X), torch.tensor(y)

def train_and_export_model():
    if not HAS_TORCH:
        print("PyTorch is not installed. Skipping training simulation.")
        return
        
    print("=== Training Compression Optimizer AI ===")
    
    # 1. Dataset & DataLoader
    X_train, y_train = create_dummy_dataset(2000)
    dataset = TensorDataset(X_train, y_train)
    loader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    # 2. Model, Loss, Optimizer
    model = CompressionOptimizerCNN()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # 3. Training Loop (Simulated for 5 epochs)
    print("Starting training (5 epochs)...")
    for epoch in range(5):
        epoch_loss = 0.0
        start = time.time()
        for batch_X, batch_y in loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        elapsed = time.time() - start
        print(f" Epoch {epoch+1} | Loss: {epoch_loss/len(loader):.4f} | Time: {elapsed:.2f}s")
        
    print("Training complete.\\n")
    
    # 4. Export to ONNX
    onnx_path = "compression_optimizer.onnx"
    print(f"Exporting trained model to {onnx_path}...")
    dummy_input = torch.randn(1, 4, 64, 64)
    torch.onnx.export(
        model, 
        dummy_input, 
        onnx_path, 
        export_params=True,
        opset_version=11, 
        do_constant_folding=True,
        input_names=['input'], 
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )
    
    file_size_mb = os.path.getsize(onnx_path) / (1024 * 1024)
    print(f"Export complete. Model size: {file_size_mb:.2f} MB")
    
    # 5. Test ONNX Inference Speed
    print("\\nTesting ONNX inference speed...")
    session = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
    
    test_input = np.random.randn(1, 4, 64, 64).astype(np.float32)
    # Warmup
    session.run(['output'], {'input': test_input})
    
    start = time.time()
    for _ in range(1000):
        _ = session.run(['output'], {'input': test_input})
    elapsed = (time.time() - start) * 1000
    print(f" -> Time to infer 1000 chunks: {elapsed:.2f} ms ({elapsed/1000:.4f} ms per chunk)")

if __name__ == '__main__':
    train_and_export_model()
