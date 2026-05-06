"""
RunPod Serverless Handler for spiritbuun TCQ llama.cpp
Supports 1M context inference with Trellis-Coded Quantization
"""

import os
import json
import subprocess
import sys
import time
import threading
from pathlib import Path
import runpod

# Configuration
LLAMA_SERVER_PATH = "/app/llama-server"
DEFAULT_MODEL_PATH = "/models/model-q4_k_4.gguf"  # Mount your model here
DEFAULT_PORT = 8000
DEFAULT_CONTEXT = 32000  # Start conservative, increase as needed
DEFAULT_BATCH_SIZE = 512

# Global process handle
llama_process = None
server_ready = False
server_start_time = None


def start_llama_server(model_path: str, context_size: int = DEFAULT_CONTEXT, batch_size: int = DEFAULT_BATCH_SIZE):
    """Start the llama-server in background"""
    global llama_process, server_ready, server_start_time
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    # Build command with TCQ optimization for 1M context
    cmd = [
        LLAMA_SERVER_PATH,
        "-m", model_path,
        "--port", str(DEFAULT_PORT),
        "-ngl", "999",                    # All layers on GPU
        "-fa", "1",                       # Flash Attention (required for >8K)
        "--threads", "2",                 # CPU helper threads
        "-ctk", "turbo3_tcq",            # TCQ for Keys
        "-ctv", "turbo3_tcq",            # TCQ for Values
        "--ctx-size", str(context_size),
        "--batch-size", str(batch_size),
        "-n", "-1",                      # Don't generate by default
    ]
    
    print(f"Starting llama-server with {context_size} context size...")
    print(f"Command: {' '.join(cmd)}")
    
    server_start_time = time.time()
    llama_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Wait for server to be ready (check logs)
    max_wait = 60  # seconds
    waited = 0
    while waited < max_wait:
        if llama_process.poll() is not None:
            # Process died
            output, _ = llama_process.communicate()
            raise RuntimeError(f"llama-server failed to start:\n{output}")
        
        time.sleep(1)
        waited += 1
        
        # Simple check - try to connect
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', DEFAULT_PORT))
            sock.close()
            if result == 0:
                server_ready = True
                print(f"✓ Server ready in {waited}s")
                break
        except:
            pass
    
    if not server_ready:
        raise TimeoutError(f"llama-server failed to start within {max_wait}s")


def make_inference_request(prompt: str, max_tokens: int = 1024, temperature: float = 0.7, **kwargs):
    """Make inference request to llama-server"""
    import requests
    
    if not server_ready:
        raise RuntimeError("Server not ready")
    
    url = f"http://localhost:{DEFAULT_PORT}/v1/completions"
    
    payload = {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": kwargs.get("top_p", 0.9),
        "top_k": kwargs.get("top_k", 40),
    }
    
    try:
        response = requests.post(url, json=payload, timeout=300)  # 5min timeout for long contexts
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Inference request failed: {e}")


def runpod_handler(job):
    """
    RunPod handler for serverless inference
    
    Input format:
    {
        "input": {
            "prompt": "Your prompt here",
            "max_tokens": 1024,
            "temperature": 0.7,
            "context_size": 32000,
            "batch_size": 512
        }
    }
    
    Output:
    {
        "output": {
            "text": "generated text",
            "tokens_generated": 256,
            "time_taken": 12.3
        }
    }
    """
    global server_ready, llama_process
    
    try:
        job_input = job["input"]
        
        # Extract parameters
        prompt = job_input.get("prompt", "")
        if not prompt:
            return {"error": "No prompt provided"}
        
        max_tokens = job_input.get("max_tokens", 1024)
        temperature = job_input.get("temperature", 0.7)
        context_size = job_input.get("context_size", DEFAULT_CONTEXT)
        batch_size = job_input.get("batch_size", DEFAULT_BATCH_SIZE)
        model_path = job_input.get("model_path", DEFAULT_MODEL_PATH)
        
        # Start server if not already running
        if not server_ready or llama_process is None:
            try:
                start_llama_server(model_path, context_size, batch_size)
            except Exception as e:
                return {"error": f"Failed to start server: {e}"}
        
        # Make inference request
        start_time = time.time()
        result = make_inference_request(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        elapsed = time.time() - start_time
        
        # Extract completion text
        if "choices" in result and len(result["choices"]) > 0:
            completion_text = result["choices"][0].get("text", "")
            completion_tokens = result.get("usage", {}).get("completion_tokens", 0)
            
            return {
                "output": {
                    "text": completion_text,
                    "tokens_generated": completion_tokens,
                    "time_taken": elapsed,
                    "model": model_path,
                    "context_size": context_size,
                }
            }
        else:
            return {"error": "Unexpected response format from server"}
            
    except Exception as e:
        return {"error": f"Handler error: {str(e)}"}


if __name__ == "__main__":
    print("Starting RunPod serverless handler for spiritbuun TCQ llama.cpp")
    print(f"TCQ context support: 1,000,000+ tokens")
    print(f"Model path: {DEFAULT_MODEL_PATH}")
    print(f"Default context: {DEFAULT_CONTEXT}")
    
    # Test if model exists
    if not os.path.exists(DEFAULT_MODEL_PATH):
        print(f"⚠️  Model not found at {DEFAULT_MODEL_PATH}")
        print("Mount your quantized model to /models/model-q4_k_4.gguf")
        print("Or pass model_path in the job input")
    
    # Start RunPod job handler
    print("✓ Handler ready")
    runpod.serverless.start({"handler": runpod_handler})
