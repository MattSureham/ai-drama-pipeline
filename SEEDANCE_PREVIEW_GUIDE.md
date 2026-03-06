# 🔧 Seedance 2.0 Preview 实战接入指南

针对 Preview 版本的限制和特性，提供实用的接入代码和最佳实践。

---

## ⚠️ Preview 版已知限制

| 功能 | Preview 状态 | 应对策略 |
|------|-------------|---------|
| **视频时长** | 限制 5-10秒 | 分段生成 + 后期拼接 |
| **分辨率** | 主要 1080p | 接受或后期超分（Topaz）|
| **原生音频** | 部分支持 | 备用 ElevenLabs 配音 |
| **批量调用** | 速率限制 | 加入队列 + 延迟重试 |
| **API 稳定性** | 无 SLA | 错误处理 + 自动重试 |
| **多模态** | 基本支持 | 9图可用，视频/音频参考或受限 |

---

## 🚀 实战代码：Preview 版适配

### 1. 增强版 SeedanceAPI 类

```python
# seedance_preview_client.py
import requests
import time
import random
from typing import List, Dict, Optional
from pathlib import Path
import base64


class SeedancePreviewClient:
    """
    Seedance 2.0 Preview 版客户端
    针对 Preview 版的限制做适配和容错
    """
    
    # 支持的第三方平台
    ENDPOINTS = {
        "piapi": {
            "url": "https://api.piapi.ai/v1/seedance",
            "model": "seedance-2.0-preview",
            "max_duration": 10,  # Preview限制
            "max_images": 9,
            "rate_limit": 10  # 每分钟请求数
        },
        "atlas": {
            "url": "https://api.atlascloud.ai/v1/video/generate",
            "model": "bytedance/seedance-2.0-preview",
            "max_duration": 8,
            "max_images": 6,
            "rate_limit": 8
        }
    }
    
    def __init__(self, api_key: str, provider: str = "piapi"):
        self.api_key = api_key
        self.config = self.ENDPOINTS.get(provider, self.ENDPOINTS["piapi"])
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.request_count = 0
        self.last_request_time = 0
    
    def _rate_limit_wait(self):
        """速率限制保护"""
        min_interval = 60 / self.config["rate_limit"]
        elapsed = time.time() - self.last_request_time
        if elapsed < min_interval:
            wait_time = min_interval - elapsed + random.uniform(0.5, 1.5)
            print(f"⏱️  速率限制等待: {wait_time:.1f}秒")
            time.sleep(wait_time)
    
    def _encode_images(self, image_paths: List[str]) -> List[str]:
        """将图片转为 base64"""
        encoded = []
        for path in image_paths[:self.config["max_images"]]:
            with open(path, "rb") as f:
                encoded.append(base64.b64encode(f.read()).decode())
        return encoded
    
    def generate(
        self,
        prompt: str,
        reference_images: List[str] = None,
        duration: int = 5,
        max_retries: int = 3,
        **kwargs
    ) -> Dict:
        """
        生成视频（带重试机制）
        """
        # Preview 版时长限制
        duration = min(duration, self.config["max_duration"])
        
        payload = {
            "model": self.config["model"],
            "prompt": prompt,
            "duration": duration,
            "resolution": "1080p",  # Preview 版优先 1080p
            "settings": {
                "audio": kwargs.get("audio", True)
            }
        }
        
        # 添加参考图
        if reference_images:
            payload["reference_images"] = self._encode_images(reference_images)
        
        # 重试机制
        for attempt in range(max_retries):
            try:
                self._rate_limit_wait()
                
                response = requests.post(
                    self.config["url"],
                    headers=self.headers,
                    json=payload,
                    timeout=300
                )
                
                self.last_request_time = time.time()
                
                # 处理速率限制错误
                if response.status_code == 429:
                    wait = int(response.headers.get("Retry-After", 60))
                    print(f"⚠️  触发速率限制，等待 {wait} 秒...")
                    time.sleep(wait)
                    continue
                
                response.raise_for_status()
                result = response.json()
                
                return {
                    "success": True,
                    "video_url": result.get("video_url") or result.get("output", {}).get("url"),
                    "duration": duration,
                    "provider": self.config["model"],
                    "metadata": result
                }
                
            except requests.exceptions.RequestException as e:
                print(f"❌ 请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait = 2 ** attempt + random.uniform(1, 3)  # 指数退避
                    print(f"⏱️  {wait:.1f} 秒后重试...")
                    time.sleep(wait)
                else:
                    return {
                        "success": False,
                        "error": str(e),
                        "attempts": max_retries
                    }
        
        return {"success": False, "error": "Max retries exceeded"}
    
    def generate_batch(
        self,
        prompts: List[Dict],
        delay_between: float = 8.0
    ) -> List[Dict]:
        """
        批量生成（带间隔）
        """
        results = []
        for i, item in enumerate(prompts):
            print(f"\n🎬 生成 {i+1}/{len(prompts)}: {item.get('shot_id', 'unknown')}")
            
            result = self.generate(
                prompt=item["prompt"],
                reference_images=item.get("reference_images"),
                duration=item.get("duration", 5)
            )
            
            results.append({
                "shot_id": item.get("shot_id"),
                **result
            })
            
            # 间隔等待
            if i < len(prompts) - 1:
                print(f"⏱️  等待 {delay_between} 秒...")
                time.sleep(delay_between)
        
        return results
```

### 2. 与 Pipeline 集成

```python
# 修改 ai_drama_pipeline_2026.py 中的 SeedanceAPI 类

from seedance_preview_client import SeedancePreviewClient

class PipelineManager2026:
    def __init__(self, use_preview=True):
        self.current_project = None
        self.seedance_client = None
        self.use_preview = use_preview
    
    def set_api_key(self, api_key: str, provider: str = "piapi"):
        """
        设置 API Key
        
        Args:
            api_key: 从 PiAPI/Atlas Cloud 获取的 key
            provider: "piapi" 或 "atlas"
        """
        if self.use_preview:
            self.seedance_client = SeedancePreviewClient(api_key, provider)
            print(f"✅ 已连接到 Seedance 2.0 Preview ({provider})")
            print(f"   限制: 最长 {self.seedance_client.config['max_duration']} 秒/视频")
        else:
            # 正式版开放后使用
            pass
    
    def generate_shot(self, shot_id: str) -> Dict:
        """生成单个镜头"""
        shot, scene = self._find_shot(shot_id)
        
        # 收集参考图
        char_refs = []
        for char_name in shot.characters:
            char = self._get_character(char_name)
            if char:
                char_refs.extend(char.reference_images[:3])
        
        # 生成
        result = self.seedance_client.generate(
            prompt=shot.generation_prompt,
            reference_images=char_refs + shot.reference_images,
            duration=shot.duration
        )
        
        if result["success"]:
            shot.status = "generated"
            shot.output_video = result["video_url"]
            self.save_project(self.current_project)
            
            print(f"✅ 生成成功: {result['video_url']}")
            print(f"   时长: {result['duration']}秒")
        else:
            print(f"❌ 生成失败: {result.get('error')}")
        
        return result
```

### 3. 分段生成策略（突破时长限制）

```python
class SegmentGenerator:
    """
    将长镜头分段生成，然后智能拼接
    解决 Preview 版 10秒限制
    """
    
    def __init__(self, client: SeedancePreviewClient):
        self.client = client
    
    def generate_long_shot(
        self,
        prompt: str,
        target_duration: int,  # 目标时长，比如 30秒
        reference_images: List[str] = None
    ) -> Dict:
        """
        分段生成长视频
        """
        segment_duration = self.client.config["max_duration"]  # 10秒
        num_segments = (target_duration + segment_duration - 1) // segment_duration
        
        print(f"🎬 分段生成: {target_duration}秒 = {num_segments}段 x {segment_duration}秒")
        
        segments = []
        for i in range(num_segments):
            print(f"\n📹 生成第 {i+1}/{num_segments} 段...")
            
            # 修改提示词，添加连续性提示
            segment_prompt = f"""
{prompt}

CONTINUITY NOTE: This is segment {i+1} of {num_segments}.
{'Opening shot' if i == 0 else 'Continuing from previous segment'}
{'Closing shot' if i == num_segments - 1 else 'Smooth transition to next'}
"""
            
            # 继承上一段的最后帧作为参考
            refs = reference_images.copy() if reference_images else []
            if i > 0 and segments[-1].get("last_frame"):
                refs.append(segments[-1]["last_frame"])
            
            result = self.client.generate(
                prompt=segment_prompt,
                reference_images=refs[:9],  # 限制9张
                duration=segment_duration
            )
            
            if result["success"]:
                segments.append(result)
                # 下载并提取最后一帧
                result["last_frame"] = self._extract_last_frame(result["video_url"])
            else:
                print(f"⚠️ 第 {i+1} 段失败，使用占位")
                segments.append(None)
        
        # 拼接视频
        if all(s and s["success"] for s in segments):
            final_video = self._stitch_segments(segments)
            return {
                "success": True,
                "video_url": final_video,
                "segments": len(segments),
                "total_duration": target_duration
            }
        else:
            return {
                "success": False,
                "error": "Some segments failed",
                "segments": segments
            }
    
    def _extract_last_frame(self, video_url: str) -> str:
        """提取视频最后一帧作为下一段参考"""
        import cv2
        import tempfile
        
        # 下载视频
        response = requests.get(video_url)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(response.content)
            video_path = f.name
        
        # 提取最后一帧
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
        ret, frame = cap.read()
        
        # 保存
        frame_path = video_path.replace(".mp4", "_last_frame.jpg")
        cv2.imwrite(frame_path, frame)
        
        cap.release()
        return frame_path
    
    def _stitch_segments(self, segments: List[Dict]) -> str:
        """智能拼接视频段"""
        # 使用 FFmpeg 拼接
        import subprocess
        
        # 创建 concat 列表文件
        with open("concat_list.txt", "w") as f:
            for seg in segments:
                f.write(f"file '{seg['video_url']}'\n")
        
        # FFmpeg 拼接
        output = "stitched_video.mp4"
        subprocess.run([
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", "concat_list.txt",
            "-c", "copy", output
        ])
        
        return output
```

---

## 🛡️ 容错与降级策略

```python
class FallbackManager:
    """
    当 Seedance 2.0 Preview 不可用时自动降级
    """
    
    PROVIDERS = [
        ("piapi_seedance2", SeedancePreviewClient, {"provider": "piapi"}),
        ("atlas_seedance2", SeedancePreviewClient, {"provider": "atlas"}),
        ("piapi_seedance15", SeedancePreviewClient, {"provider": "piapi", "model": "seedance-1.5-pro"}),
        ("runway_gen3", RunwayClient, {}),  # 备用
    ]
    
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        self.clients = {}
    
    def generate_with_fallback(self, prompt: str, **kwargs) -> Dict:
        """
        逐级尝试，直到成功
        """
        for name, client_class, config in self.PROVIDERS:
            try:
                print(f"🔄 尝试使用: {name}")
                
                if name not in self.clients:
                    key = self.api_keys.get(name.split("_")[0])  # piapi, atlas, etc.
                    self.clients[name] = client_class(key, **config)
                
                result = self.clients[name].generate(prompt, **kwargs)
                
                if result["success"]:
                    print(f"✅ 使用 {name} 成功")
                    result["provider_used"] = name
                    return result
                else:
                    print(f"⚠️  {name} 失败: {result.get('error')}")
                    
            except Exception as e:
                print(f"❌ {name} 异常: {e}")
                continue
        
        return {"success": False, "error": "All providers failed"}
```

---

## 📊 Preview 版最佳实践

### 1. 项目规划

```python
# 根据 Preview 限制规划项目
PROJECT_CONFIG = {
    "shot_duration": 8,        # Preview 最大 10，留余量用 8
    "segments_per_scene": 3,   # 每场景3段，总长 24秒
    "daily_quota": 100,        # PiAPI 日限额
    "concurrent_limit": 2,     # 并发数限制
}
```

### 2. 错误处理

```python
def robust_generate(prompt, max_retries=3, fallback_enabled=True):
    """健壮的生成函数"""
    for attempt in range(max_retries):
        try:
            result = client.generate(prompt)
            if result["success"]:
                return result
            
            # 特定错误处理
            if "rate limit" in result.get("error", "").lower():
                time.sleep(60)  # 等一分钟
                continue
                
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
    
    # 全部失败，使用 fallback
    if fallback_enabled:
        return fallback_manager.generate_with_fallback(prompt)
    
    return {"success": False}
```

### 3. 监控与日志

```python
import json
from datetime import datetime

class GenerationLogger:
    """记录所有生成尝试，便于分析"""
    
    def __init__(self, log_file: str = "generation_log.jsonl"):
        self.log_file = log_file
    
    def log(self, shot_id: str, result: Dict, metadata: Dict = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "shot_id": shot_id,
            "success": result.get("success"),
            "provider": result.get("provider_used", "unknown"),
            "duration": result.get("duration"),
            "error": result.get("error"),
            "metadata": metadata
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
```

---

## 🚀 快速开始

```python
# 1. 安装依赖
# pip install requests opencv-python

# 2. 获取 API Key（PiAPI）
# https://piapi.ai → Sign Up → Dashboard → API Keys

# 3. 测试代码
from seedance_preview_client import SeedancePreviewClient

client = SeedancePreviewClient(
    api_key="your-piapi-key",
    provider="piapi"
)

result = client.generate(
    prompt="Cinematic shot of a woman walking in the rain, film noir style",
    reference_images=["woman_ref.jpg"],
    duration=8
)

if result["success"]:
    print(f"视频生成成功: {result['video_url']}")
else:
    print(f"失败: {result['error']}")
```

---

**准备好接入 Preview 版了吗？需要我帮你：**
1. 生成测试用的参考图组织脚本？
2. 创建批量生成队列管理器？
3. 写视频自动拼接脚本？