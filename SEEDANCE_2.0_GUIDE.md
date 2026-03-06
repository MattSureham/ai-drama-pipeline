# 🎬 AI短剧制作 Pipeline - Seedance 2.0 版

> **重要**: 正确品牌名为 **Seedance 2.0** (ByteDance出品)，不是 SeaDance。

---

## 🆕 Seedance 2.0 核心特性（2026年2月发布）

| 特性 | 传统AI视频 | Seedance 2.0 |
|------|-----------|--------------|
| **品牌** | Runway, Pika | **ByteDance (TikTok母公司)** |
| **输入** | 单图/文本 | **9图 + 3视频 + 3音频 + 文本** |
| **输出时长** | 4-16秒 | **15秒/次** |
| **音频** | 后期配音 | **原生生成** (对白+环境音+音乐) |
| **角色一致** | LoRA训练 | **参考图直接锁定** |
| **运镜** | 基础推拉 | **导演级控制** |
| **分辨率** | 1080p | **2K** |
| **多镜头** | 单镜头 | **一次生成多镜头+剪辑** |

---

## 🚀 快速开始

### 1. 基础用法

```python
from ai_drama_pipeline_2026 import PipelineManager2026

pm = PipelineManager2026()

# 创建项目 - 指定Seedance 2.0
project = pm.create_project(
    name="我的短剧",
    video_backend="seedance-2.0",
    resolution="2k"
)

# 添加角色 - 无需训练LoRA！
pm.add_character(
    name="女主",
    description="25岁程序员",
    reference_images=["face1.jpg", "face2.jpg", "face3.jpg"]  # 最多9张
)

# 添加运镜控制的镜头
pm.add_shot(
    scene_id="scene_001",
    description="女主惊讶特写",
    shot_type="closeup",
    camera_move="zoom_in",      # 推镜头
    camera_angle="low_angle",   # 仰拍
    dialogue="这怎么可能？",     # Seedance原生生成语音！
    duration=10
)

# 生成
pm.set_api_key("your-seedance-api-key")
pm.generate_scene("scene_001")
```

---

## 📡 Seedance 2.0 API 结构

```python
POST https://api.seedance.ai/v1/generations

{
  "model": "seedance-2.0-pro",
  "prompt": "cinematic shot...",
  "reference_images": ["char1.jpg", "char2.jpg"],  # 最多9张
  "reference_videos": ["motion.mp4"],              # 最多3个，15s/个
  "reference_audios": ["voice_tone.mp3"],          # 最多3个，15s/个
  "settings": {
    "resolution": "2k",
    "duration": 15,
    "audio": true,
    "language": "zh"
  }
}
```

---

## 🎯 Seedance 2.0 与其他工具对比

```
2024年方案:                    2026年 Seedance 2.0:
───────────                    ─────────────────────
Midjourney/SD                  Seedream (ByteDance)
    ↓                              ↓
LoRA训练角色 (2小时)            上传9张参考图 (即时)
    ↓                              ↓
Runway Gen-3 (4s)              Seedance (15s)
    ↓                              ↓
ElevenLabs配音                 原生音频生成
    ↓                              ↓
剪映后期合成                    多镜头自动剪辑
    ↓                              ↓
总工时: 2-3天                   总工时: 2-3小时
成本: $50-100/集               成本: $5-15/集
```

---

## 🏢 官方资源

- **官网**: https://seed.bytedance.com/en/seedance2_0
- **API文档**: https://seedance2.ai/docs
- **第三方接入**: https://fal.ai/seedance-2.0
- **在线体验**: https://seedance2.ai/

---

## 📚 相关文件

| 文件 | 说明 |
|------|------|
| `ai_drama_pipeline_2026.py` | **Seedance 2.0版** - 推荐新项目使用 |
| `ai_drama_pipeline.py` | 2024版 - 支持Runway/Luma/ComfyUI |
| `comfyui_workflow_generator.py` | ComfyUI批量工作流生成 |

---

**注意**: 请认准 **Seedance** 拼写，避免与早期SeaDance概念混淆。
