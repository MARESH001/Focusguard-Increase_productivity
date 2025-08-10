#!/usr/bin/env python3
"""
BERT Installation and Verification Script for FocusGuard
This script helps install and verify the BERT-based classification system
"""

import subprocess
import sys
import os
import importlib

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detected. Python 3.8+ required.")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible!")
    return True

def install_requirements():
    """Install required packages"""
    print("\n📦 Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def verify_imports():
    """Verify that all required packages can be imported"""
    print("\n🔍 Verifying package imports...")
    
    required_packages = [
        'torch',
        'transformers',
        'sentence_transformers',
        'sklearn',
        'numpy',
        'fastapi',
        'motor',
        'websockets'
    ]
    
    failed_imports = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} - OK")
        except ImportError as e:
            print(f"❌ {package} - FAILED: {e}")
            failed_imports.append(package)
    
    if failed_imports:
        print(f"\n⚠️  Failed imports: {', '.join(failed_imports)}")
        return False
    
    print("✅ All packages imported successfully!")
    return True

def test_bert_initialization():
    """Test BERT model initialization"""
    print("\n🧠 Testing BERT initialization...")
    
    try:
        # Test basic imports
        from transformers import pipeline
        from sentence_transformers import SentenceTransformer
        import torch
        
        print("✅ Basic imports successful")
        
        # Test GPU availability
        if torch.cuda.is_available():
            print(f"🚀 GPU detected: {torch.cuda.get_device_name(0)}")
            device = 0
        else:
            print("💻 Using CPU (GPU not available)")
            device = -1
        
        # Test sentiment analyzer
        print("📊 Initializing sentiment analyzer...")
        sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            device=device
        )
        print("✅ Sentiment analyzer initialized")
        
        # Test text model
        print("🔤 Initializing text understanding model...")
        text_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Text understanding model initialized")
        
        # Test classification
        print("🎯 Testing classification...")
        test_text = "Python programming tutorial for beginners"
        embedding = text_model.encode(test_text)
        print(f"✅ Text embedding created (shape: {embedding.shape})")
        
        # Test sentiment
        result = sentiment_analyzer(test_text[:512])
        print(f"✅ Sentiment analysis: {result[0]}")
        
        print("\n🎉 BERT system test successful!")
        return True
        
    except Exception as e:
        print(f"❌ BERT test failed: {e}")
        print("\n💡 Troubleshooting tips:")
        print("1. Check internet connection (models need to download)")
        print("2. Ensure sufficient disk space (~600MB)")
        print("3. Check memory availability")
        print("4. Try running with CPU only if GPU issues occur")
        return False

def main():
    """Main installation process"""
    print("🚀 FocusGuard BERT Installation Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        print("\n❌ Installation failed. Please check the errors above.")
        sys.exit(1)
    
    # Verify imports
    if not verify_imports():
        print("\n❌ Package verification failed. Please check the errors above.")
        sys.exit(1)
    
    # Test BERT
    if not test_bert_initialization():
        print("\n❌ BERT test failed. Please check the errors above.")
        print("\n🔄 The system will fall back to basic keyword classification.")
        print("   You can still use FocusGuard, but without AI-powered features.")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Installation Complete!")
    print("\n🚀 Next steps:")
    print("1. Start the backend: python main.py")
    print("2. Start the frontend: pnpm dev (in frontend folder)")
    print("3. Run the window monitor: python window_monitor.py")
    print("\n📚 For more information, see BERT_CLASSIFIER_README.md")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ FocusGuard BERT system is ready to use!")
        else:
            print("\n⚠️  Installation completed with warnings. Check above for details.")
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
