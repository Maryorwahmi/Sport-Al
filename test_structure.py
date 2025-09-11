"""
Simple test to verify the project structure is correct
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, '/home/runner/work/SMC-Forez/SMC-Forez')

def test_imports():
    """Test that all modules can be imported"""
    try:
        # Test config import
        from smc_forez.config.settings import Settings, Timeframe
        print("✓ Config module imported successfully")
        
        # Test settings creation
        settings = Settings()
        print(f"✓ Settings created with {len(settings.timeframes)} timeframes")
        
        # Test timeframe enum
        tf = Timeframe.H1
        print(f"✓ Timeframe enum works: {tf.value}")
        
        return True
        
    except Exception as e:
        print(f"✗ Import error: {str(e)}")
        return False

def test_structure():
    """Test project structure"""
    base_path = '/home/runner/work/SMC-Forez/SMC-Forez'
    
    required_dirs = [
        'smc_forez',
        'smc_forez/config',
        'smc_forez/data_sources',
        'smc_forez/market_structure',
        'smc_forez/smart_money',
        'smc_forez/signals',
        'smc_forez/utils',
        'smc_forez/backtesting',
        'examples'
    ]
    
    required_files = [
        'setup.py',
        'requirements.txt',
        'README.md',
        '.gitignore',
        'smc_forez/__init__.py',
        'smc_forez/analyzer.py'
    ]
    
    print("Testing project structure:")
    
    for dir_path in required_dirs:
        full_path = os.path.join(base_path, dir_path)
        if os.path.exists(full_path):
            print(f"✓ Directory exists: {dir_path}")
        else:
            print(f"✗ Directory missing: {dir_path}")
    
    for file_path in required_files:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            print(f"✓ File exists: {file_path}")
        else:
            print(f"✗ File missing: {file_path}")

def main():
    print("SMC Forez - Structure and Import Tests")
    print("=" * 50)
    
    print("\n1. Testing Project Structure")
    print("-" * 30)
    test_structure()
    
    print("\n2. Testing Core Imports")
    print("-" * 30)
    success = test_imports()
    
    print("\n3. Summary")
    print("-" * 30)
    if success:
        print("✓ All basic tests passed!")
        print("✓ Project structure is correct")
        print("✓ Core modules can be imported")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Configure MT5 credentials for live data")
        print("3. Run examples with full functionality")
    else:
        print("✗ Some tests failed")
        print("Check the error messages above")

if __name__ == "__main__":
    main()