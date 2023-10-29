# AITuber Mirai Chan V2.0

## Installation Guide for Faster Whisper

### Prerequisites:
Ensure you have the following software installed:
- **PyTorch**: [PyTorch Official Website](https://pytorch.org/)
- **CUDA Toolkit**: [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)
- **cuDNN**: [NVIDIA cuDNN](https://developer.nvidia.com/cuDNN)

### cuDNN Setup:
After downloading cuDNN, extract and copy its contents to:
```
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v1x.x
```
Make sure to add the following paths to your system's PATH variable:
- `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v1x.x\bin`
- `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v1x.x\libnvvp`
- `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v1x.x\include`

---

## Troubleshooting

### Could not load library cudnn_ops_infer64_8.dll. Error code 126:
```
Could not load library cudnn_ops_infer64_8.dll. Error code 126
Please make sure cudnn_ops_infer64_8.dll is in your library path!
```
**Description**: This error indicates that a required library couldn't be loaded or found.
**Cause**: cuDNN might not be installed or the path hasn't been set properly.

### OMP: Error #15:
```
OMP: Error #15: Initializing libiomp5md.dll, but found libiomp5md.dll already initialized.
```
**Description**: The same library (`libiomp5md.dll`) has been initialized multiple times.
**Cause**: An incompatible version of numpy is installed.
**Solution**: Upgrade numpy by executing:
```
pip install numpy --upgrade
```