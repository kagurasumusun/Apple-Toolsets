import numpy as np
import json
import os
from pathlib import Path

def generate_training_data(num_samples=5000):
    """
    特徴量 (Features):
    1. alpha_zero_ratio: 透過ピクセルの割合
    2. unique_color_ratio: 色の多様性 (少ないほどRLEやパレット向き)
    3. edge_density: エッジの複雑さ (高いほど文字やアイコン)
    
    ターゲット (Labels):
    0: RLE (単色・透明)
    1: LZFSE (UI・アイコン)
    2: Raw / ASTC (写真・グラデーション)
    """
    np.random.seed(42)
    X = np.random.rand(num_samples, 3).astype(np.float32)
    y = np.zeros(num_samples, dtype=int)
    
    for i in range(num_samples):
        alpha, color, edge = X[i]
        if alpha > 0.9 and color < 0.1:
            y[i] = 0 # ほぼ透明で単色 -> RLE
        elif edge > 0.5 and color < 0.5:
            y[i] = 1 # エッジが多く色数が適度 -> LZFSE
        else:
            y[i] = 2 # 複雑 -> Raw/ASTC
            
    return X, y

def train_numpy_nn():
    print("=== Training Micro AI with Pure NumPy ===")
    X, y = generate_training_data(10000)
    
    # One-hot encoding for targets
    num_classes = 3
    y_onehot = np.zeros((y.size, num_classes))
    y_onehot[np.arange(y.size), y] = 1

    # Network architecture: 3 -> 16 -> 3
    W1 = np.random.randn(3, 16) * 0.1
    b1 = np.zeros(16)
    W2 = np.random.randn(16, 3) * 0.1
    b2 = np.zeros(3)

    learning_rate = 0.1
    epochs = 100

    def relu(x): return np.maximum(0, x)
    def relu_deriv(x): return (x > 0).astype(float)
    def softmax(x): 
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)

    print("Starting training loop...")
    for epoch in range(epochs):
        # Forward pass
        z1 = np.dot(X, W1) + b1
        a1 = relu(z1)
        z2 = np.dot(a1, W2) + b2
        probs = softmax(z2)

        # Loss (Categorical Cross-Entropy)
        loss = -np.mean(np.sum(y_onehot * np.log(probs + 1e-8), axis=1))

        # Backward pass
        dz2 = probs - y_onehot
        dW2 = np.dot(a1.T, dz2) / X.shape[0]
        db2 = np.sum(dz2, axis=0) / X.shape[0]

        da1 = np.dot(dz2, W2.T)
        dz1 = da1 * relu_deriv(z1)
        dW1 = np.dot(X.T, dz1) / X.shape[0]
        db1 = np.sum(dz1, axis=0) / X.shape[0]

        # Update weights
        W1 -= learning_rate * dW1
        b1 -= learning_rate * db1
        W2 -= learning_rate * dW2
        b2 -= learning_rate * db2

        if (epoch+1) % 20 == 0:
            preds = np.argmax(probs, axis=1)
            acc = np.mean(preds == y)
            print(f"Epoch {epoch+1}/{epochs} - Loss: {loss:.4f} - Acc: {acc*100:.2f}%")

    # Save trained weights
    weights = {
        "W1": W1.tolist(),
        "b1": b1.tolist(),
        "W2": W2.tolist(),
        "b2": b2.tolist()
    }
    
    out_dir = Path("actool_linux/data")
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / "micro_ai_weights.json", "w") as f:
        json.dump(weights, f)
        
    print(f"\\nModel successfully trained and saved to {out_dir / 'micro_ai_weights.json'}")

if __name__ == "__main__":
    train_numpy_nn()
