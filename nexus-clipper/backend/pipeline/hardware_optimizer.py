"""Omniscient Hardware Optimizer"""

import os, platform
from utils.logger import get_logger
log = get_logger("pipeline_hwopt")

class HardwareOptimizer:
    def __init__(self):
        self.hw = self._detect()

    def _detect(self):
        try:
            import psutil
            ram = psutil.virtual_memory().total / (1024**3)
        except:
            ram = 8.0
        cpu = os.cpu_count() or 4
        gpu, gpu_name, vram = False, "None", 0
        try:
            import torch
            if torch.cuda.is_available():
                gpu = True
                gpu_name = torch.cuda.get_device_name(0)
                vram = torch.cuda.get_device_properties(0).total_mem / (1024**3)
        except:
            pass
        return {"cpu_count": cpu, "total_ram_gb": round(ram, 1), "gpu_available": gpu, "gpu_name": gpu_name, "gpu_vram_gb": round(vram, 1), "os": platform.system()}

    def get_optimal_config(self):
        hw = self.hw
        return {"hardware": hw, "config": {"parallel_agents": min(hw["cpu_count"]//2, 8), "micro_batch": hw["total_ram_gb"] < 8, "use_gpu": hw["gpu_available"], "ffmpeg_threads": max(hw["cpu_count"]//2, 2)}}

    def get_hardware_info(self):
        return self.hw

hardware_optimizer = HardwareOptimizer()
