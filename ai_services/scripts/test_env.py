# test_env.py
import sys
print(f"Python: {sys.version}")
print(f"Executable: {sys.executable}")

try:
    import insightface
    print(f"✅ insightface: {insightface.__version__}")
except ImportError as e:
    print(f"❌ InsightFace: {e}")

try:
    import cv2
    print(f"✅ OpenCV: {cv2.__version__}")
except ImportError as e:
    print(f"❌ OpenCV: {e}")

try:
    import numpy as np
    print(f"✅ NumPy: {np.__version__}")
except ImportError as e:
    print(f"❌ NumPy: {e}")

print("\n🎉 Environment is ready!")