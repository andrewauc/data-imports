#!/usr/bin/env python3
"""
Test script to verify the National Gas API and InfluxDB connectivity
"""

import os
import sys
import requests
from datetime import datetime


def test_api_connection():
    """Test connection to National Gas API"""
    print("Testing National Gas API connection...")
    try:
        url = "https://api.nationalgas.com/operationaldata/v1/gasquality/latestdata"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"✓ API connection successful (Status: {response.status_code})")
            data = response.json()
            print(f"  Response type: {type(data)}")
            
            # Print sample of response structure
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:5]}")
            elif isinstance(data, list):
                print(f"  List length: {len(data)}")
                if len(data) > 0:
                    print(f"  First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'N/A'}")
            
            return True
        else:
            print(f"✗ API returned status code: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ API connection failed: {e}")
        return False


def test_influxdb_connection():
    """Test connection to InfluxDB"""
    print("\nTesting InfluxDB connection...")
    
    # Check if influxdb-client is installed
    try:
        from influxdb_client import InfluxDBClient
    except ImportError:
        print("✗ influxdb-client not installed. Run: pip install influxdb-client")
        return False
    
    # Get credentials from environment
    url = os.getenv("INFLUXDB_URL")
    token = os.getenv("INFLUXDB_TOKEN")
    org = os.getenv("INFLUXDB_ORG")
    bucket = os.getenv("INFLUXDB_BUCKET")
    
    if not all([url, token, org, bucket]):
        print("✗ Missing InfluxDB configuration. Please set environment variables:")
        print("  - INFLUXDB_URL")
        print("  - INFLUXDB_TOKEN")
        print("  - INFLUXDB_ORG")
        print("  - INFLUXDB_BUCKET")
        return False
    
    try:
        client = InfluxDBClient(url=url, token=token, org=org)
        
        # Test connection with ping
        if client.ping():
            print(f"✓ InfluxDB connection successful")
            print(f"  URL: {url}")
            print(f"  Org: {org}")
            print(f"  Bucket: {bucket}")
            
            # Try to verify bucket exists
            try:
                buckets_api = client.buckets_api()
                bucket_obj = buckets_api.find_bucket_by_name(bucket)
                if bucket_obj:
                    print(f"  ✓ Bucket '{bucket}' found")
                else:
                    print(f"  ⚠ Bucket '{bucket}' not found - may need to be created")
            except Exception as e:
                print(f"  ⚠ Could not verify bucket: {e}")
            
            client.close()
            return True
        else:
            print("✗ InfluxDB ping failed")
            client.close()
            return False
            
    except Exception as e:
        print(f"✗ InfluxDB connection failed: {e}")
        return False


def test_meltano_installation():
    """Test if Meltano is installed and configured"""
    print("\nTesting Meltano installation...")
    
    # Check if meltano is in PATH
    import shutil
    if not shutil.which("meltano"):
        print("✗ Meltano not found in PATH")
        print("  Install with: pip install meltano")
        return False
    
    print("✓ Meltano is installed")
    
    # Check if meltano.yml exists
    if not os.path.exists("meltano.yml"):
        print("✗ meltano.yml not found in current directory")
        return False
    
    print("✓ meltano.yml found")
    
    # Check if plugins directory exists
    if os.path.exists("plugins/tap-nationalgas") and os.path.exists("plugins/target-influxdb"):
        print("✓ Custom plugins directory found")
        return True
    else:
        print("⚠ Custom plugins directory not complete")
        return True  # Not critical for initial test


def main():
    """Run all tests"""
    print("=" * 50)
    print("Meltano ETL Environment Test")
    print("=" * 50)
    print()
    
    # Load .env file if it exists
    if os.path.exists(".env"):
        print("Loading .env file...")
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value
        print("✓ Environment loaded from .env")
        print()
    else:
        print("⚠ .env file not found - using environment variables")
        print()
    
    results = {
        "API": test_api_connection(),
        "InfluxDB": test_influxdb_connection(),
        "Meltano": test_meltano_installation(),
    }
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✓ All tests passed! You're ready to run the pipeline.")
        print("\nNext step: meltano run nationalgas-to-influxdb")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
