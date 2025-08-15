from typing import Dict, Any
import os
import ollama
import time

# Initialize client with debug info
ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
print(f"[OLLAMA DEBUG] Initializing client with host: {ollama_host}")

_client = ollama.Client(host=ollama_host)

def chat(prompt: str, model: str | None = None) -> Dict[str, Any]:
    start_time = time.time()
    
    try:
        # Determine model to use
        use_model = (model or os.getenv("OLLAMA_MODEL") or "llama3").strip()
        
        print(f"[OLLAMA DEBUG] Starting chat request")
        print(f"[OLLAMA DEBUG] Host: {ollama_host}")
        print(f"[OLLAMA DEBUG] Model: {use_model}")
        print(f"[OLLAMA DEBUG] Prompt length: {len(prompt)} characters")
        
        # Test connection first
        print(f"[OLLAMA DEBUG] Attempting to connect to Ollama server...")
        
        # Make the actual request
        res = _client.chat(model=use_model, messages=[{"role":"user","content":prompt}])
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Get response content
        response_content = res.get("message", {}).get("content", "")
        
        print(f"[OLLAMA DEBUG] SUCCESS - Connection established!")
        print(f"[OLLAMA DEBUG] Response time: {response_time:.2f} seconds")
        print(f"[OLLAMA DEBUG] Response length: {len(response_content)} characters")
        print(f"[OLLAMA DEBUG] Response preview: {response_content[:100]}..." if len(response_content) > 100 else f"[OLLAMA DEBUG] Full response: {response_content}")
        
        return {
            "ok": True, 
            "reply": response_content, 
            "model": use_model,
            "response_time": response_time
        }
        
    except ConnectionError as e:
        print(f"[OLLAMA DEBUG] CONNECTION ERROR - Cannot reach Ollama server")
        print(f"[OLLAMA DEBUG] Host attempted: {ollama_host}")
        print(f"[OLLAMA DEBUG] Error details: {str(e)}")
        print(f"[OLLAMA DEBUG] This likely means:")
        print(f"[OLLAMA DEBUG] - Tailscale VPN is not working")
        print(f"[OLLAMA DEBUG] - IP not whitelisted yet")
        print(f"[OLLAMA DEBUG] - Server is down")
        return {"ok": False, "error": f"Connection failed to {ollama_host}: {e}"}
        
    except TimeoutError as e:
        print(f"[OLLAMA DEBUG] TIMEOUT ERROR - Server took too long to respond")
        print(f"[OLLAMA DEBUG] Host: {ollama_host}")
        print(f"[OLLAMA DEBUG] Error details: {str(e)}")
        print(f"[OLLAMA DEBUG] This might mean the server is overloaded or network is slow")
        return {"ok": False, "error": f"Timeout connecting to {ollama_host}: {e}"}
        
    except Exception as e:
        response_time = time.time() - start_time
        print(f"[OLLAMA DEBUG] GENERAL ERROR after {response_time:.2f} seconds")
        print(f"[OLLAMA DEBUG] Host: {ollama_host}")
        print(f"[OLLAMA DEBUG] Model: {use_model}")
        print(f"[OLLAMA DEBUG] Error type: {type(e).__name__}")
        print(f"[OLLAMA DEBUG] Error details: {str(e)}")
        
        # Additional debug for common issues
        if "connection refused" in str(e).lower():
            print(f"[OLLAMA DEBUG] Connection refused - server may not be running")
        elif "timeout" in str(e).lower():
            print(f"[OLLAMA DEBUG] Timeout - network or server issue")
        elif "unauthorized" in str(e).lower():
            print(f"[OLLAMA DEBUG] Unauthorized - authentication issue")
        elif "not found" in str(e).lower():
            print(f"[OLLAMA DEBUG] Not found - check host URL or model name")
            
        return {"ok": False, "error": f"Ollama error: {e}"}

# Test connection on startup (optional)
def test_connection():
    """Test the Ollama connection on startup"""
    print(f"[OLLAMA DEBUG] Testing connection on startup...")
    result = chat("Hello", "llama3")
    if result["ok"]:
        print(f"[OLLAMA DEBUG] Startup connection test PASSED")
    else:
        print(f"[OLLAMA DEBUG] Startup connection test FAILED: {result['error']}")
    return result["ok"]

# Uncomment the line below if you want to test connection when the module loads
# test_connection()
