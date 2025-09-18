#!/usr/bin/env python3
"""
Setup script for PayScale URL Parser
Run this to set up the environment and test the installation
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}:")
        print(f"Command: {command}")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"❌ Python 3.7+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"✓ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def create_directories():
    """Create necessary directories"""
    directories = ['output', 'data']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}/")

def test_installation():
    """Test that everything is working"""
    print(f"\n🧪 Testing installation...")
    
    try:
        # Test imports
        import pandas as pd
        import numpy as np
        print("✓ Required packages imported successfully")
        
        # Test parser
        from payscale_parser import PayScaleURLParser
        parser = PayScaleURLParser()
        print("✓ PayScale parser imported successfully")
        
        # Test with sample URL
        test_url = "https://www.payscale.com/cost-of-living-calculator/California-San-Francisco"
        result = parser.parse_url(test_url)
        
        if result['location_state'] == 'California' and result['location_city'] == 'San Francisco':
            print("✓ URL parsing test passed")
            return True
        else:
            print("❌ URL parsing test failed")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 PayScale URL Parser Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        print("\n💡 Try running with: python -m pip install -r requirements.txt")
        sys.exit(1)
    
    # Test installation
    if not test_installation():
        print("\n❌ Setup completed with errors. Please check the error messages above.")
        sys.exit(1)
    
    print(f"\n🎉 Setup completed successfully!")
    print(f"\n📋 Quick Start:")
    print(f"   python run_parser.py sample_data.csv")
    print(f"\n📖 For more options:")
    print(f"   python run_parser.py --help")
    print(f"\n📁 Sample data file: sample_data.csv")
    print(f"📁 Results will be saved in: output/")

if __name__ == "__main__":
    main()