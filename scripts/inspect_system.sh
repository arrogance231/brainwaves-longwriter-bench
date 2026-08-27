#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_JSON="${OUT_JSON:-$ROOT_DIR/reports/environment.json}"
OUT_MD="${OUT_MD:-$ROOT_DIR/reports/environment.md}"
VLLM_IMAGE="${VLLM_IMAGE:-vllm-rocm:0.28.0-gfx942}"
mkdir -p "$(dirname "$OUT_JSON")"
OUT_JSON="$OUT_JSON" OUT_MD="$OUT_MD" VLLM_IMAGE="$VLLM_IMAGE" python3 - <<'PY'
import base64, json, os, platform, shutil, subprocess
from pathlib import Path

def run(cmd, timeout=20):
    try:
        p=subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout)
        return {"returncode":p.returncode, "stdout":p.stdout.strip(), "stderr":p.stderr.strip()}
    except Exception as e:
        return {"returncode":-1, "stdout":"", "stderr":repr(e)}

def text(cmd): return run(cmd)["stdout"]

result={
  "captured_utc": text("date -u +%Y-%m-%dT%H:%M:%SZ"),
  "host": {"uname": platform.platform(), "kernel": text("uname -r"), "python": platform.python_version()},
  "gpu": run("rocm-smi --showproductname --showmeminfo vram --showdriverversion --json"),
  "rocminfo": run("rocminfo | grep -E 'Name:|Marketing Name:|gfx[0-9]+' | head -80"),
  "cpu": run("lscpu"), "memory": run("free -h"), "numa": run("numactl -H"),
  "pci": run("lspci -nn"), "storage": run("lsblk -o NAME,MODEL,SIZE,FSTYPE,MOUNTPOINT,ROTA"),
  "filesystem": run("df -hT / /root/qwen"),
  "compiler": {"gcc":text("gcc --version | head -1"), "clang":text("clang --version | head -1"), "cmake":text("cmake --version | head -1")},
  "docker": {"version":run("docker version --format '{{.Server.Version}}'"), "image":run("docker image inspect "+os.environ["VLLM_IMAGE"]+" --format '{{json .RepoDigests}}'"), "running":run("docker ps --format '{{.Names}} {{.Image}} {{.Status}} {{.Ports}}'" )},
}
probe="""python - <<'PY2'
import importlib.util, json, sys
out={"python":sys.version}
for n in ["torch","transformers","vllm","sglang","aiter","huggingface_hub","safetensors"]:
 try:
  s=importlib.util.find_spec(n)
  if not s: out[n]=None; continue
  m=__import__(n); out[n]={"version":getattr(m,"__version__","unknown"),"file":getattr(m,"__file__","")}
 except Exception as e: out[n]={"error":repr(e)}
try:
 import torch
 out["torch_hip"]=torch.version.hip
except Exception as e: out["torch_hip_error"]=repr(e)
print(json.dumps(out))
PY2"""
encoded=base64.b64encode(probe.encode()).decode()
result["container_runtime"]=run("docker run --rm --entrypoint bash "+os.environ["VLLM_IMAGE"]+" -lc \"echo "+encoded+" | base64 -d | bash\"", timeout=90)
Path(os.environ["OUT_JSON"]).write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
md=[]
md.append("# Environment audit\n\nCaptured: `"+result["captured_utc"]+"`\n")
md.append("## Host\n\n```text\n"+result["host"]["uname"]+"\nkernel "+result["host"]["kernel"]+"\nPython "+result["host"]["python"]+"\n```\n")
md.append("## GPU / ROCm\n\n```text\n"+result["gpu"]["stdout"]+"\n```\n")
md.append("## Memory / NUMA / storage\n\n### RAM\n```text\n"+result["memory"]["stdout"]+"\n```\n### NUMA\n```text\n"+result["numa"]["stdout"]+"\n```\n### Filesystem\n```text\n"+result["filesystem"]["stdout"]+"\n```\n")
md.append("## Container runtime\n\nImage: `"+os.environ["VLLM_IMAGE"]+"`\n\n```text\n"+result["container_runtime"]["stdout"]+"\n"+result["container_runtime"]["stderr"]+"\n```\n")
md.append("Raw structured output: [`environment.json`](environment.json).\n")
Path(os.environ["OUT_MD"]).write_text("\n".join(md))
PY
echo "wrote $OUT_JSON and $OUT_MD"
