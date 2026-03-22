#!/usr/bin/env python3
"""
Test script to verify vLLM server is working correctly.
"""
import argparse
import json
import sys

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx


def test_health(base_url: str) -> bool:
    """Test if server is healthy"""
    print("Testing server health...")
    try:
        response = httpx.get(f"{base_url}/health", timeout=10.0)
        if response.status_code == 200:
            print("  ✓ Server is healthy")
            return True
        else:
            print(f"  ✗ Server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        return False


def test_models(base_url: str) -> bool:
    """Test listing available models"""
    print("\nListing models...")
    try:
        response = httpx.get(f"{base_url}/v1/models", timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])
            for model in models:
                print(f"  ✓ Model: {model.get('id', 'unknown')}")
            return len(models) > 0
        else:
            print(f"  ✗ Failed to list models: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_completion(base_url: str) -> bool:
    """Test chat completion"""
    print("\nTesting chat completion...")
    try:
        response = httpx.post(
            f"{base_url}/v1/chat/completions",
            json={
                "model": "Qwen/Qwen2.5-14B-Instruct-AWQ",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello from vLLM!' in exactly 5 words."}
                ],
                "max_tokens": 50,
                "temperature": 0.7,
            },
            timeout=60.0,
        )

        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            print(f"  ✓ Response: {content}")

            # Print usage stats
            usage = data.get("usage", {})
            print(f"  ✓ Tokens - prompt: {usage.get('prompt_tokens', 'N/A')}, "
                  f"completion: {usage.get('completion_tokens', 'N/A')}")
            return True
        else:
            print(f"  ✗ Request failed: {response.status_code}")
            print(f"    {response.text[:200]}")
            return False
    except httpx.TimeoutException:
        print("  ✗ Request timed out (model may still be loading)")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test vLLM server")
    parser.add_argument(
        "--url",
        default="http://localhost:8001",
        help="vLLM server URL (default: http://localhost:8001)"
    )
    args = parser.parse_args()

    base_url = args.url.rstrip("/")

    print("=" * 50)
    print("vLLM Server Test")
    print("=" * 50)
    print(f"Server URL: {base_url}")
    print()

    results = []

    # Run tests
    results.append(("Health Check", test_health(base_url)))
    results.append(("Model List", test_models(base_url)))
    results.append(("Chat Completion", test_completion(base_url)))

    # Summary
    print("\n" + "=" * 50)
    print("Test Results")
    print("=" * 50)

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("All tests passed! vLLM server is ready.")
        print(f"\nUpdate your backend .env:")
        print(f"  VLLM_BASE_URL={base_url}/v1")
    else:
        print("Some tests failed. Check the server logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()
