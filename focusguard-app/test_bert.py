#!/usr/bin/env python3
"""
Test script for BERT functionality.
This script tests the BERT-based content classification to ensure it works
correctly with the updated dependencies.
"""

import sys
import os

# Add the current directory to Python path
sys.path.append('.')

def test_bert_imports():
    """Test if BERT-related libraries can be imported"""
    print("🧪 Testing BERT Library Imports")
    print("=" * 40)
    
    try:
        import transformers
        print(f"✅ transformers: {transformers.__version__}")
    except ImportError as e:
        print(f"❌ transformers import failed: {e}")
        return False
    
    try:
        import sentence_transformers
        print(f"✅ sentence-transformers: {sentence_transformers.__version__}")
    except ImportError as e:
        print(f"❌ sentence-transformers import failed: {e}")
        return False
    
    try:
        import huggingface_hub
        print(f"✅ huggingface-hub: {huggingface_hub.__version__}")
    except ImportError as e:
        print(f"❌ huggingface-hub import failed: {e}")
        return False
    
    try:
        import torch
        print(f"✅ torch: {torch.__version__}")
        print(f"🔧 CUDA available: {torch.cuda.is_available()}")
    except ImportError as e:
        print(f"❌ torch import failed: {e}")
        return False
    
    return True

def test_bert_classifier():
    """Test the BERT-based content classifier"""
    print("\n🎯 Testing BERT Content Classifier")
    print("=" * 40)
    
    try:
        from main import AdvancedContentClassifier
        print("✅ Successfully imported AdvancedContentClassifier")
    except ImportError as e:
        print(f"❌ Failed to import AdvancedContentClassifier: {e}")
        return False
    
    try:
        classifier = AdvancedContentClassifier()
        print("✅ AdvancedContentClassifier initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize classifier: {e}")
        return False
    
    # Test content classification
    test_titles = [
        "YouTube - Watch Videos",
        "Google Docs - Document Editor",
        "Stack Overflow - Programming Questions",
        "Facebook - Social Media",
        "GitHub - Code Repository",
        "Microsoft Teams - Video Meeting",
        "Netflix - Watch Movies",
        "LinkedIn - Professional Network"
    ]
    
    print("\n📊 Testing content classification:")
    for title in test_titles:
        try:
            result = classifier.classify_content(title)
            print(f"📝 '{title[:30]}...' -> {result['category']} (confidence: {result['confidence']:.2f})")
        except Exception as e:
            print(f"❌ Failed to classify '{title}': {e}")
            return False
    
    return True

def test_sentence_embeddings():
    """Test sentence embeddings generation"""
    print("\n🔤 Testing Sentence Embeddings")
    print("=" * 40)
    
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ SentenceTransformer loaded successfully")
        
        # Test embedding generation
        sentences = ["This is a test sentence.", "Another test sentence."]
        embeddings = model.encode(sentences)
        print(f"✅ Generated embeddings shape: {embeddings.shape}")
        
        return True
    except Exception as e:
        print(f"❌ Sentence embeddings test failed: {e}")
        return False

def test_huggingface_hub():
    """Test huggingface hub functionality"""
    print("\n🏠 Testing HuggingFace Hub")
    print("=" * 40)
    
    try:
        from huggingface_hub import hf_hub_download, list_models
        print("✅ HuggingFace Hub functions imported successfully")
        
        # Test model listing (this should work without downloading)
        try:
            models = list_models(search="sentence-transformers", limit=1)
            print(f"✅ Model listing works: Found {len(models)} models")
        except Exception as e:
            print(f"⚠️ Model listing failed (this might be expected): {e}")
        
        return True
    except ImportError as e:
        print(f"❌ HuggingFace Hub import failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting BERT Functionality Tests")
    print("=" * 50)
    
    # Test imports
    if not test_bert_imports():
        print("\n❌ BERT imports failed. Check dependencies.")
        sys.exit(1)
    
    # Test HuggingFace Hub
    if not test_huggingface_hub():
        print("\n❌ HuggingFace Hub test failed.")
        sys.exit(1)
    
    # Test sentence embeddings
    if not test_sentence_embeddings():
        print("\n❌ Sentence embeddings test failed.")
        sys.exit(1)
    
    # Test classifier
    if not test_bert_classifier():
        print("\n❌ BERT classifier test failed.")
        sys.exit(1)
    
    print("\n🎉 All BERT tests passed!")
    print("✅ BERT functionality is working correctly.")
    print("🎯 Content classification is ready for use.")

if __name__ == "__main__":
    main()
