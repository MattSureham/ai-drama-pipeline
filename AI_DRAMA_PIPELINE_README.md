# 🎬 AI短剧制作Pipeline系统

一套完整的AI短剧自动化制作工具，包含项目管理、提示词生成、ComfyUI工作流导出等功能。

---

## 📦 系统组成

```
workspace/
├── ai_drama_pipeline.py          # 核心Pipeline管理器
├── comfyui_workflow_generator.py # ComfyUI工作流生成器
└── ai_drama_projects/            # 项目文件夹（自动生成）
    └── 你的项目/
        ├── project.json          # 项目数据
        ├── characters/           # 角色资产
        │   ├── reference/        # 参考图
        │   └── lora_training/    # LoRA训练数据
        ├── scenes/               # 场景
        │   └── scene_001/
        │       └── shots/        # 镜头画面
        ├── audio/                # 音频资产
        ├── video/                # 视频片段
        └── final/                # 最终输出
```

---

## 🚀 快速开始

### 1. 基础用法

```python
from ai_drama_pipeline import PipelineManager, WorkflowTemplates

# 创建Pipeline管理器
pm = PipelineManager()

# 方式一：从模板创建（推荐新手）
project = WorkflowTemplates.romance_drama("咖啡店爱情故事")

# 方式二：手动创建
project = pm.create_project(
    name="科幻短片",
    genre="scifi", 
    style="cyberpunk, neon lights, futuristic"
)
```

### 2. 添加角色

```python
pm.add_character(
    name="小雅",
    description="25岁插画师，短发，文艺气质",
    attributes={
        "age": "25",
        "hair": "short brown hair",
        "eyes": "big expressive eyes",
        "style": "artistic, casual, sweater",
        "personality": "gentle, creative"
    },
    trigger_word="XiaoYa"  # LoRA触发词
)
```

### 3. 创建场景和镜头

```python
# 添加场景
scene = pm.add_scene(
    title="初次相遇",
    description="小雅在咖啡店画画，不小心打翻咖啡",
    location="cozy coffee shop",
    time_of_day="afternoon",
    mood="romantic"
)

# 添加镜头（提示词自动生成）
shot = pm.add_shot(
    scene_id=scene.scene_id,
    description="小雅专注画画的中景",
    shot_type="medium",  # wide, medium, closeup, extreme_closeup
    characters=["小雅"],
    action="sitting by window, sketching in notebook",
    emotion="peaceful"
)
```

**自动生成的提示词示例：**
```
正提示词：
masterpiece, best quality, highly detailed, 8k resolution, 
medium shot, waist up, balanced composition, 
(XiaoYa:1.2), 25 years old, short brown hair, big expressive eyes, artistic, casual, sweater, 
in cozy coffee shop, sitting by window, sketching in notebook, 
warm lighting, golden hour, soft shadows, afternoon light, 
cinematic, film grain, sharp focus

负提示词：
bad anatomy, extra fingers, blurry, low quality, watermark, 
signature, deformed, ugly, mutation...
```

### 4. 导出到ComfyUI

```python
# 生成ComfyUI配置文件
config_path = pm.export_for_comfyui()
print(f"配置文件已生成: {config_path}")

# 查看批量生成任务
prompts = pm.generate_batch_prompts()
for p in prompts:
    print(f"{p['shot_id']}: {p['positive'][:80]}...")
```

### 5. 生成ComfyUI工作流JSON

```python
from comfyui_workflow_generator import generate_comfyui_workflow, save_workflow

# 生成工作流
workflow = generate_comfyui_workflow(
    prompts=pm.generate_batch_prompts(),
    lora_path="characters/lora_training/XiaoYa_v1.safetensors",
    use_ipadapter=True,
    use_controlnet=True
)

# 保存
save_workflow(workflow, "my_drama_workflow.json")
```

---

## 📋 完整制作流程

### 第一阶段：项目初始化（5分钟）

```python
from ai_drama_pipeline import PipelineManager, WorkflowTemplates

# 选择模板或新建
pm = PipelineManager()
project = WorkflowTemplates.romance_drama("我的短剧")
# 或: project = pm.create_project("我的短剧", genre="romance")

# 添加角色（关键！决定一致性）
pm.add_character(name="女主", ...)
pm.add_character(name="男主", ...)

# 添加3-5个场景
for i, scene_desc in enumerate(scene_descriptions):
    pm.add_scene(title=f"场景{i+1}", description=scene_desc, ...)
    
# 为每个场景添加3-8个镜头
pm.add_shot(scene_id="scene_001", description="...", ...)
```

### 第二阶段：角色资产建设（30分钟-2小时）

**2.1 收集角色参考图**
```bash
cd ai_drama_projects/我的短剧/characters/reference/
# 放置15-30张角色照片，要求：
# - 多角度（正面、侧面、45度）
# - 不同表情（笑、严肃、惊讶）
# - 不同光线
```

**2.2 训练LoRA（保持角色一致的关键）**

```bash
# 使用Kohya_ss训练
python train_network.py \
  --pretrained_model_name="SDXL_base.safetensors" \
  --train_data_dir="characters/lora_training/女主" \
  --output_dir="characters/lora_output" \
  --network_dim=32 \
  --network_alpha=16 \
  --resolution=1024 \
  --max_train_epochs=10
```

或使用云端训练：
- **Civitai Trainer**: 上传图片，自动训练
- **Replicate**: 一键LoRA训练
- **Google Colab**: 免费GPU训练

**2.3 测试LoRA效果**

```python
# 更新角色资产
pm.current_project.characters[0].lora_path = "characters/lora_output/女主_v1.safetensors"
pm.save_project(pm.current_project)
```

### 第三阶段：批量生成图像（使用ComfyUI）

**3.1 生成ComfyUI工作流**

```python
from comfyui_workflow_generator import generate_comfyui_workflow, save_workflow

workflow = generate_comfyui_workflow(
    prompts=pm.generate_batch_prompts(),
    lora_path="characters/lora_output/女主_v1.safetensors"
)

save_workflow(workflow, "batch_generation.json")
```

**3.2 在ComfyUI中配置**

1. 打开ComfyUI
2. Load → 选择 `batch_generation.json`
3. 修改以下节点：
   - **CheckpointLoader**: 选择你的SDXL模型
   - **LoraLoader**: 确认LoRA路径正确
   - **LoadImage (IP-Adapter)**: 上传角色面部参考图
   - **ControlNetLoader**: 选择OpenPose模型

**3.3 高级技巧：保持角色一致性**

```python
# 使用IP-Adapter（推荐）
# 在ComfyUI中添加：
# 1. Load Image节点 → 上传角色面部参考图
# 2. IPAdapter节点 → 连接到Conditioning
# 3. 权重建议：0.5-0.7

# 使用InstantID（更强的一致性）
# 安装ComfyUI_InstantID插件
# 只需1张面部照片即可保持极高一致性
```

### 第四阶段：视频生成

**4.1 图生视频工具选择**

| 工具 | 优点 | 适用场景 |
|------|------|----------|
| **Runway Gen-3** | 人物一致性最好 | 人物特写、对话场景 |
| **Luma Dream Machine** | 物理效果真实 | 动作场景、环境镜头 |
| **Pika Labs** | 创意控制多 | 特效场景、转场 |

**4.2 Runway Gen-3工作流**

```python
# 批量导出为Runway可用的格式
import os
from pathlib import Path

project_dir = Path("ai_drama_projects/我的短剧")
scenes_dir = project_dir / "scenes"

# 为每个场景的选中图片生成视频
for scene_dir in scenes_dir.glob("scene_*"):
    shots_dir = scene_dir / "shots"
    for img_path in shots_dir.glob("*.png"):
        print(f"上传到Runway: {img_path}")
        print(f"提示词: 使用项目中的动作描述")
```

**Runway参数建议：**
- Motion Brush: 手动选择运动区域
- Camera Control: 固定镜头或减少运动（保持角色稳定）
- General Motion: 3-5（过高会变形）

### 第五阶段：后期制作

**5.1 配音生成**

```python
# 使用ElevenLabs API
import requests

def generate_voice(text: str, voice_id: str, output_path: str):
    url = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": "your_api_key"}
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    response = requests.post(url, json=data, headers=headers)
    with open(output_path, "wb") as f:
        f.write(response.content)

# 为每个镜头生成配音
for scene in pm.current_project.scenes:
    for shot in scene.shots:
        if shot.dialogue:
            generate_voice(
                shot.dialogue,
                voice_id="XB0fDUnXU5powFXDhCwa",  # 选择的声音
                output_path=f"audio/voice/{shot.shot_id}.mp3"
            )
```

**5.2 剪辑**

推荐使用 **DaVinci Resolve**（免费）：
1. 导入所有视频片段
2. 按场景组织时间线
3. 添加配音轨道
4. 使用AI语音同步（如果需要）
5. 添加字幕
6. 调色输出

---

## 🎨 提示词工程技巧

### 角色一致性公式

```
(角色触发词:1.2) + 外貌描述 + 服装 + 情绪 + 动作 + 环境 + 光照 + 质量词

示例：
(XiaoYa:1.2), 25 years old woman, short brown hair, big expressive eyes,
wearing cream sweater and jeans, gentle smile, 
sitting by window in cozy coffee shop,
warm afternoon light, soft bokeh background,
masterpiece, best quality, cinematic, 8k
```

### 加权语法（SDXL/ComfyUI）

```
(关键词:1.2)     # 增强1.2倍
(关键词:0.8)     # 减弱0.8倍
[关键词]          # 减弱1.1倍
((关键词))        # 增强1.21倍（1.1*1.1）
```

### 情绪光照对照表

| 情绪 | 光照关键词 | 色彩 |
|------|-----------|------|
| 浪漫 | warm glow, golden hour, soft focus | 橙黄、暖色 |
| 紧张 | high contrast, dramatic shadows | 蓝灰、高对比 |
| 悲伤 | cool tones, overcast, blue hour | 蓝紫、低饱和 |
| 神秘 | low key, rim lighting, fog | 暗绿、剪影 |
| 开心 | bright, soft shadows, vibrant | 明亮、高饱和 |

---

## 🔧 高级功能

### 批量修改提示词

```python
# 为所有镜头添加特定风格
for scene in pm.current_project.scenes:
    for shot in scene.shots:
        shot.prompt += ", film noir style, black and white"
        
pm.save_project(pm.current_project)
```

### 生成进度报告

```python
progress = pm.get_progress()
print(f"总进度: {progress['progress_percentage']:.1f}%")
print(f"已完成镜头: {progress['completed_shots']}/{progress['total_shots']}")
print(f"状态分布: {progress['status_breakdown']}")
```

### 多项目切换

```python
# 保存当前
pm.save_project(pm.current_project)

# 加载另一个
project2 = pm.load_project("另一个项目")
pm.current_project = project2
```

---

## 💡 最佳实践

### ✅ 应该做的

1. **角色触发词要独特**：避免使用常见词汇如"girl"，用"XiaoYa"或"FemaleLead"
2. **训练LoRA**：15-30张高质量角色照片，一致性提升80%
3. **分镜要详细**：每个镜头的景别、动作、情绪都影响生成质量
4. **批量生成**：同一角色的镜头一起生成，保持风格一致
5. **保存所有版本**：每次生成保存project.json，方便回滚

### ❌ 避免的事

1. **不要频繁更换基础模型**：会显著改变角色外观
2. **不要忽略负提示词**：负面提示词和正面同样重要
3. **不要一次性生成太多**：ComfyUI内存有限，建议10-20个镜头一批
4. **不要跳过参考图**：IP-Adapter/InstantID是保持一致性的关键

---

## 🐛 常见问题

### Q: 角色在不同镜头中长得不一样？

**A:** 使用以下组合拳：
1. 训练角色LoRA（最有效）
2. 使用IP-Adapter（面部特征锁定）
3. 使用InstantID（单图换脸级一致性）
4. 固定种子（seed）生成

### Q: 手部总是变形？

**A:** 
1. 使用ADetailer插件自动修复
2. 避免手部特写，用中景代替
3. 添加负提示词：bad hands, mutated hands
4. 使用ControlNet OpenPose手动指定手部姿态

### Q: 生成速度太慢？

**A:**
1. 降低分辨率：1024→768
2. 减少采样步数：30→20
3. 使用更快的采样器：DPM++ 2M Karras
4. 启用xformers/flash attention
5. 使用批量生成（一次生成多张）

### Q: 视频生成时人物变形？

**A:**
1. 减少Runway的Motion参数
2. 使用Character Consistency功能
3. 分段生成：先测3秒，稳定后再生成完整版
4. 关键帧锁定：首尾帧使用同一张图片

---

## 🚀 进阶：自动化集成

### 与DuckVibe集成

```python
# 使用DuckVibe自动完成整个流程
task = """
使用ai_drama_pipeline创建一个新短剧项目：
1. 类型：科幻爱情
2. 2个角色：赛博朋克风格
3. 5个场景
4. 每个场景3-4个镜头
5. 生成ComfyUI工作流
6. 输出完整项目配置
"""

# DuckVibe会自动调用PipelineManager完成任务
```

### API化部署

```python
from fastapi import FastAPI
from ai_drama_pipeline import PipelineManager

app = FastAPI()
pm = PipelineManager()

@app.post("/create_project")
def create_project(config: dict):
    project = pm.create_project(**config)
    return {"project_id": project.name, "status": "created"}

@app.get("/{project_id}/prompts")
def get_prompts(project_id: str):
    pm.load_project(project_id)
    return pm.generate_batch_prompts()
```

---

## 📚 资源推荐

### 学习资源
- [ComfyUI官方文档](https://comfyanonymous.github.io/ComfyUI_examples/)
- [LoRA训练指南](https://github.com/kohya-ss/sd-scripts)
- [Runway教程](https://runwayml.com/guides/)

### 社区
- Civitai: 模型分享
- Reddit r/StableDiffusion: 技术讨论
- 哔哩哔哩: 中文AI绘画教程

---

## 📄 License

MIT License - 自由使用和修改

---

**Happy Creating! 🎬✨**
