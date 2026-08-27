# Environment audit

Captured: `2026-08-27T14:51:21Z`

## Host

```text
Linux-7.0.0-27-generic-x86_64-with-glibc2.43
kernel 7.0.0-27-generic
Python 3.14.4
```

## GPU / ROCm

```text
```

The MI300X is presented as a virtual function; a separate firmware revision was
not exposed by `rocm-smi`/`rocminfo` in this environment.

## Memory / NUMA / storage

### RAM
```text
total        used        free      shared  buff/cache   available
Mem:           235Gi        11Gi       4.1Gi        20Mi       222Gi       224Gi
Swap:             0B          0B          0B
```
### NUMA
```text
available: 1 nodes (0)
node 0 cpus: 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19
node 0 size: 241605 MB
node 0 free: 4187 MB
node distances:
node     0
   0:   10
```
### Filesystem
```text
Filesystem     Type  Size  Used Avail Use% Mounted on
/dev/vda1      ext4  698G  408G  291G  59% /
/dev/vda1      ext4  698G  408G  291G  59% /
```

## Container runtime

Image: `vllm-rocm:0.28.0-gfx942`

```text
{"python": "3.12.3 (main, Jul 15 2026, 23:46:41) [GCC 13.3.0]", "torch": {"version": "2.12.0+git6bbd260", "file": "/opt/venv/lib/python3.12/site-packages/torch/__init__.py"}, "transformers": {"version": "5.16.1", "file": "/opt/venv/lib/python3.12/site-packages/transformers/__init__.py"}, "vllm": {"version": "0.28.0", "file": "/opt/venv/lib/python3.12/site-packages/vllm/__init__.py"}, "sglang": null, "aiter": {"error": "RuntimeError(\"Get GPU arch from rocminfo failed: Command '['/opt/rocm-7.2.3/bin/rocminfo']' returned non-zero exit status 1.\")"}, "huggingface_hub": {"version": "1.28.0", "file": "/opt/venv/lib/python3.12/site-packages/huggingface_hub/__init__.py"}, "safetensors": {"version": "0.8.0", "file": "/opt/venv/lib/python3.12/site-packages/safetensors/__init__.py"}, "torch_hip": "7.2.53211"}
[aiter] import [module_aiter_core] under /opt/venv/lib/python3.12/site-packages/aiter/jit/module_aiter_core.so
```

Raw structured output: [`environment.json`](environment.json).
