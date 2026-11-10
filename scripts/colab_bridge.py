"""
Bridge script to communicate with Colab MCP server without opening browser.
Uses standard library only (urllib, json, subprocess, base64).
"""
import subprocess
import json
import urllib.request
import urllib.error
import base64
import os
import sys

MCP_URL = "https://colaboratory.googleapis.com/mcp"
PROJECT_ID = "vaka-taxi"

_CACHED_TOKEN = None
_CACHED_TIME = 0

def get_token():
    global _CACHED_TOKEN, _CACHED_TIME
    import time
    now = time.time()
    if _CACHED_TOKEN and (now - _CACHED_TIME < 3000):
        return _CACHED_TOKEN

    adc_path = os.path.expandvars(r"%APPDATA%\gcloud\application_default_credentials.json")
    if os.path.exists(adc_path):
        try:
            with open(adc_path, "r", encoding="utf-8") as f:
                adc = json.load(f)
            data = urllib.parse.urlencode({
                "client_id": adc["client_id"],
                "client_secret": adc["client_secret"],
                "refresh_token": adc["refresh_token"],
                "grant_type": "refresh_token"
            }).encode("utf-8")
            req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                _CACHED_TOKEN = res["access_token"]
                _CACHED_TIME = now
                return _CACHED_TOKEN
        except Exception as e:
            print(f"[!] Direct token refresh failed: {e}", file=sys.stderr)

    # Fallback to subprocess if direct refresh fails
    cmd = ["gcloud.cmd", "auth", "application-default", "print-access-token"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True)
        _CACHED_TOKEN = res.stdout.strip()
        _CACHED_TIME = now
        return _CACHED_TOKEN
    except Exception:
        cmd = ["gcloud", "auth", "application-default", "print-access-token"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True)
        _CACHED_TOKEN = res.stdout.strip()
        _CACHED_TIME = now
        return _CACHED_TOKEN

def call_mcp_raw(token, method, params=None, msg_id=1, timeout=600):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {token}",
        "X-Goog-User-Project": PROJECT_ID,
        "MCP-Protocol-Version": "2026-07-28",
        "Mcp-Method": method
    }
    body = {
        "jsonrpc": "2.0",
        "method": method,
        "id": msg_id,
        "params": params or {}
    }
    req = urllib.request.Request(MCP_URL, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8")
            # Parse possible SSE streaming response or json
            lines = [line for line in data.splitlines() if line.startswith("data: ")]
            if lines:
                last_data = lines[-1][len("data: "):]
                return json.loads(last_data)
            return json.loads(data)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="replace")
        print(f"[!] HTTP Error {e.code}: {err_msg}", file=sys.stderr)
        raise

def call_tool(token, tool_name, arguments, msg_id=1, timeout=600):
    return call_mcp_raw(token, "tools/call", {"name": tool_name, "arguments": arguments}, msg_id=msg_id, timeout=timeout)

def list_runtimes(token):
    res = call_tool(token, "list_runtimes", {})
    try:
        content = res["result"]["content"][0]["text"]
        return json.loads(content).get("runtimes", [])
    except Exception:
        return []

def get_active_runtime(token):
    runtimes = list_runtimes(token)
    if runtimes:
        return runtimes[0]["name"]
    return None

def ensure_active_runtime(token):
    rt = get_active_runtime(token)
    if rt:
        return rt
    print("⚡ No hay máquina activa. Creando una nueva en Colab...", flush=True)
    for spec in [
        {"variant": "VARIANT_GPU", "accelerator": "T4", "shape": "SHAPE_STANDARD"},
        {"variant": "VARIANT_CPU", "accelerator": "NONE", "shape": "SHAPE_STANDARD"}
    ]:
        try:
            res = call_tool(token, "create_runtime", {"runtime": {"runtimeSpec": spec}})
            content = res.get("result", {}).get("content", [{}])[0].get("text", "")
            if content and "name" in content:
                data = json.loads(content)
                print(f"✅ Máquina creada: {data['name']} ({spec['variant']} {spec['accelerator']})", flush=True)
                return data["name"]
        except Exception:
            pass
    raise RuntimeError("No se pudo crear un runtime en Colab")

def execute_remote(token, runtime, code, msg_id=1, timeout=600):
    res = call_tool(token, "execute_code", {"runtime": runtime, "code": code}, msg_id=msg_id, timeout=timeout)
    try:
        # Check structuredContent or content
        struct = res.get("result", {}).get("structuredContent", {})
        stdout = struct.get("stdout", "")
        stderr = struct.get("stderr", "")
        error = struct.get("error", None)
        if error:
            print(f"[ERROR] {error}", file=sys.stderr)
        if stdout:
            print(stdout, end="")
        if stderr:
            print(stderr, end="", file=sys.stderr)
        return struct
    except Exception as ex:
        print(f"[!] Parse error: {ex}, raw: {res}", file=sys.stderr)
        return res

def upload_file(token, runtime, local_path, remote_path, chunk_size=500000):
    """Uploads local file to Colab remote filesystem in base64 chunks."""
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Local file not found: {local_path}")
    
    file_size = os.path.getsize(local_path)
    print(f"Uploading {local_path} ({file_size} bytes) -> {remote_path}...")
    
    # Init remote file
    execute_remote(token, runtime, f"open('{remote_path}', 'wb').close()")
    
    with open(local_path, "rb") as f:
        idx = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            b64 = base64.b64encode(chunk).decode("ascii")
            code = f"""
import base64
with open('{remote_path}', 'ab') as f:
    f.write(base64.b64decode('{b64}'))
"""
            execute_remote(token, runtime, code)
            idx += len(chunk)
            print(f"  {idx}/{file_size} bytes ({int(idx*100/file_size)}%)...")
    print(f"✅ Upload complete: {remote_path}")

def download_file(token, runtime, remote_path, local_path):
    """Downloads remote file from Colab filesystem to local path."""
    print(f"Downloading {remote_path} -> {local_path}...")
    code = f"""
import base64, os
if os.path.exists('{remote_path}'):
    with open('{remote_path}', 'rb') as f:
        print('___B64_START___' + base64.b64encode(f.read()).decode('ascii') + '___B64_END___')
else:
    print('___NOT_FOUND___')
"""
    res = call_tool(token, "execute_code", {"runtime": runtime, "code": code})
    stdout = res.get("result", {}).get("structuredContent", {}).get("stdout", "")
    if "___NOT_FOUND___" in stdout:
        raise FileNotFoundError(f"Remote file not found: {remote_path}")
    if "___B64_START___" in stdout:
        b64_data = stdout.split("___B64_START___")[1].split("___B64_END___")[0].strip()
        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(base64.b64decode(b64_data))
        print(f"✅ Download complete: {local_path} ({os.path.getsize(local_path)} bytes)")
    else:
        raise RuntimeError(f"Unexpected response downloading file: {stdout[:200]}")

if __name__ == "__main__":
    t = get_token()
    rt = get_active_runtime(t)
    print(f"Active runtime: {rt}")
