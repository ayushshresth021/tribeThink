import modal

app = modal.App("tribethink")

image = modal.Image.debian_slim(python_version="3.11").pip_install("torch")


@app.function(gpu="T4", image=image)
def hello_gpu() -> str:
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return f"TribeThink workers online. Device: {device}"


@app.local_entrypoint()
def main():
    result = hello_gpu.remote()
    print(result)
