$ErrorActionPreference = "Stop"
$models = "C:\AIEngineer\Tools\ComfyUI\models"
New-Item -ItemType Directory -Force -Path "$models\diffusion_models", "$models\text_encoders", "$models\vae" | Out-Null

curl.exe -L -C - "https://huggingface.co/Comfy-Org/flux2-klein/resolve/main/split_files/diffusion_models/flux-2-klein-4b.safetensors" -o "$models\diffusion_models\flux-2-klein-4b.safetensors"
curl.exe -L -C - "https://huggingface.co/Comfy-Org/flux2-klein/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors" -o "$models\text_encoders\qwen_3_4b.safetensors"
curl.exe -L -C - "https://huggingface.co/Comfy-Org/flux2-dev/resolve/main/split_files/vae/flux2-vae.safetensors" -o "$models\vae\flux2-vae.safetensors"

Write-Host "FLUX.2 [klein] 4B model files complete."
