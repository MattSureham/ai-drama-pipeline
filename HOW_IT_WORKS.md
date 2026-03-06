# 🔧 AI Drama Pipeline - 完整工作原理详解

本文档详细解释Pipeline的每个组件如何工作，以及它们之间如何协作。

---

## 📋 目录

1. [整体架构概览](#一整体架构概览)
2. [数据模型层](#二数据模型层)
3. [提示词引擎](#三提示词引擎)
4. [API封装层](#四api封装层)
5. [Pipeline管理器](#五pipeline管理器)
6. [完整工作流程](#六完整工作流程)
7. [实际使用示例](#七实际使用示例)

---

## 一、整体架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户层 (User)                             │
│  - 创建项目                                                      │
│  - 添加角色/场景/镜头                                            │
│  - 触发生成                                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PipelineManager2026                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  职责：                                                    │   │
│  │  - 项目生命周期管理（创建/保存/加载）                        │   │
│  │  - 协调各组件工作                                          │   │
│  │  - 导出配置到外部工具（ComfyUI/Seedance API）                │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   数据模型层     │ │   提示词引擎     │ │   API封装层     │
│  Character      │ │ SeedancePrompt  │ │  SeedanceAPI    │
│  Scene          │ │   Engineer      │ │                 │
│  Shot           │ │                 │ │  ComfyUIWorkflow│
│  Project        │ │  PromptRefiner  │ │     Generator   │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    外部服务 (External Services)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Seedance 2.0│  │  ComfyUI    │  │  ElevenLabs │              │
│  │  API        │  │  (本地/云端) │  │  (语音)     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、数据模型层

### 2.1 核心数据类

```python
@dataclass
class Project:
    """项目 - 最高级容器"""
    name: str                    # 项目名称
    video_backend: str           # 使用什么生成器
    characters: List[Character]  # 角色列表
    scenes: List[Scene]          # 场景列表
```

**作用**：一个Project代表一部完整的短剧。所有角色、场景、镜头都归属这个项目。

```python
@dataclass
class Character:
    """角色 - 保持一致的实体"""
    name: str
    reference_images: List[str]  # 关键！最多9张参考图
    trigger_word: str            # 提示词中的触发词
```

**作用**：定义"谁"出现在短剧中。Seedance 2.0通过上传reference_images来锁定角色外貌，不需要训练LoRA。

```python
@dataclass
class Scene:
    """场景 - 时间+地点的容器"""
    scene_id: str        # 唯一ID (如 "scene_001")
    location: str        # 地点描述
    time_of_day: str     # 时间 (morning/noon/night...)
    mood: str            # 情绪氛围
    shots: List[Shot]    # 场景内的镜头列表
```

**作用**：一个Scene代表短剧中的一个"场次"。比如"咖啡店内午后"是一个Scene，包含多个镜头。

```python
@dataclass
class Shot:
    """镜头 - 最基本的生成单元"""
    shot_id: str         # 唯一ID (如 "scene_001_shot_001")
    description: str     # 镜头描述
    shot_type: str       # wide/medium/closeup
    camera_move: str     # 运镜方式
    camera_angle: str    # 拍摄角度
    dialogue: str        # 对白（Seedance会生成语音）
    duration: int        # 时长（秒）
    generation_prompt: str  # 自动生成的完整提示词
```

**作用**：Shot是实际生成视频的最小单位。一个Shot对应Seedance API的一次调用。

### 2.2 数据模型如何协作

```
Project (一部短剧)
    ├── Character (角色A)
    │       └── reference_images: ["face1.jpg", "face2.jpg", ...]
    │
    ├── Character (角色B)
    │       └── reference_images: ["face3.jpg", "face4.jpg", ...]
    │
    ├── Scene (场景1: 咖啡店)
    │       ├── Shot (镜头1: 全景)
    │       │       ├── characters: ["角色A"]
    │       │       ├── camera_move: "static"
    │       │       └── generation_prompt: "自动生成..."
    │       │
    │       ├── Shot (镜头2: 特写)
    │       │       ├── characters: ["角色A", "角色B"]
    │       │       ├── camera_move: "zoom_in"
    │       │       └── dialogue: "你好"
    │       │
    │       └── Shot (镜头3: 中景)
    │               └── ...
    │
    └── Scene (场景2: 公园)
            └── ...
```

---

## 三、提示词引擎

### 3.1 SeedancePromptEngineer 工作原理

```python
class SeedancePromptEngineer:
    def generate_shot_prompt(self, shot: Shot, scene: Scene) -> str:
        # 1. 基础质量词
        quality = "masterpiece, best quality, cinematic..."
        
        # 2. 角色描述（从Character获取）
        characters = "(XiaoYa:1.2), 25 years old, short hair..."
        
        # 3. 运镜描述（从预定义词汇表获取）
        camera = "medium shot, tracking shot, follows subject"
        
        # 4. 光影描述（根据time_of_day + emotion）
        lighting = "golden hour, warm tones, soft shadows"
        
        # 5. 组合成完整提示词
        return f"{quality}, {camera}, {characters}, {lighting}..."
```

**输入**：Shot对象 + Scene对象  
**输出**：优化后的英文提示词

### 3.2 提示词生成流程

```
用户输入:
  shot.description = "女主惊讶特写"
  shot.shot_type = "closeup"
  shot.emotion = "surprised"
  scene.time_of_day = "afternoon"

        ↓

SeedancePromptEngineer 处理:
  1. shot_type "closeup" → "close-up shot, head and shoulders, emotional"
  2. emotion "surprised" + time "afternoon" → "golden hour, warm tones, dramatic lighting"
  3. characters → "(CharacterName:1.2), age, hair, style..."

        ↓

生成的提示词:
  "masterpiece, best quality, close-up shot, head and shoulders, 
   emotional, (XiaoYa:1.2), 25 years old, short brown hair,
   surprised expression, golden hour, warm tones, dramatic lighting,
   cinematic, 8k resolution"
```

### 3.3 音频提示词生成

```python
def generate_audio_prompt(self, shot: Shot, scene: Scene) -> str:
    """
    Seedance 2.0 特殊功能：同时生成视频+音频
    """
    parts = []
    
    # 对白
    if shot.dialogue:
        parts.append(f"character speaking: '{shot.dialogue}'")
    
    # 环境音
    if shot.ambient_sound:
        parts.append(f"ambient: {shot.ambient_sound}")
    
    # 背景音乐
    if shot.music_mood:
        parts.append(f"background music: {self.AUDIO_TEMPLATES[shot.music_mood]}")
    
    return "; ".join(parts)
    # 输出: "character speaking: '你好'; ambient: coffee shop noise; 
    #        background music: soft romantic piano"
```

---

## 四、API封装层

### 4.1 SeedanceAPI 工作原理

```python
class SeedanceAPI:
    API_ENDPOINT = "https://api.seedance.ai/v1/generations"
    
    def generate_video(self, prompt, reference_images, ...):
        payload = {
            "model": "seedance-2.0-pro",
            "prompt": prompt,
            "reference_images": reference_images[:9],  # 最多9张
            "reference_videos": reference_videos[:3],   # 最多3个
            "reference_audios": reference_audios[:3],   # 最多3个
            "settings": {
                "resolution": "2k",
                "duration": min(duration, 15),  # 最大15秒
                "audio": True  # 关键！启用原生音频
            }
        }
        
        response = requests.post(self.API_ENDPOINT, json=payload)
        return response.json()  # 包含生成的video_url
```

### 4.2 API调用流程

```
PipelineManager.generate_shot() 被调用
            ↓
    收集参考图:
      - 从Character获取角色参考图
      - 从Shot获取镜头特定参考图
            ↓
    SeedancePromptEngineer 生成提示词
            ↓
    SeedanceAPI.generate_video() 调用API
            ↓
    返回结果:
      {
        "video_url": "https://.../video.mp4",
        "duration": 10,
        "resolution": "2048x1080"
      }
            ↓
    更新Shot.status = "generated"
    保存到 project.json
```

---

## 五、Pipeline管理器

### 5.1 PipelineManager2026 核心职责

```python
class PipelineManager2026:
    def __init__(self):
        self.current_project: Project = None  # 当前项目
        self.seedance_api: SeedanceAPI = None  # API客户端
    
    # ========== 项目生命周期 ==========
    def create_project(self, name, ...) -> Project
    def save_project(self, project)
    def load_project(self, name) -> Project
    
    # ========== 资产管理 ==========
    def add_character(self, name, reference_images, ...) -> Character
    def add_scene(self, title, ...) -> Scene
    def add_shot(self, scene_id, description, ...) -> Shot
    
    # ========== 生成控制 ==========
    def generate_shot(self, shot_id) -> Dict
    def generate_scene(self, scene_id) -> List[Dict]
    
    # ========== 导出功能 ==========
    def export_seedance_config(self) -> Dict
```

### 5.2 目录结构管理

```python
def _create_project_structure(self, project: Project):
    """
    自动创建标准化的项目目录
    """
    base = Path(project.output_dir)  # ai_drama_projects/项目名称/
    
    dirs = [
        "characters/reference_images",   # 角色参考图
        "characters/reference_videos",   # 角色动作参考
        "characters/voice_clones",       # 语音克隆
        "scenes/{scene_id}/shots",       # 场景镜头
        "scenes/{scene_id}/assets",      # 场景资产
        "audio/bgm",                     # 背景音乐
        "audio/sfx",                     # 音效
        "audio/voice",                   # 配音
        "video/raw",                     # 原始生成视频
        "video/edited",                  # 剪辑后视频
        "final",                         # 最终成片
        "exports"                        # 多平台导出
    ]
    
    for d in dirs:
        (base / d).mkdir(parents=True, exist_ok=True)
```

创建后的结构：
```
ai_drama_projects/我的短剧/
├── project_2026.json              # 项目数据（自动保存）
├── characters/
│   ├── reference_images/          # 放角色照片
│   ├── reference_videos/          # 放动作参考视频
│   └── voice_clones/              # ElevenLabs语音克隆
├── scenes/
│   └── scene_001/
│       ├── shots/                 # 生成的视频
│       └── assets/                # 场景特定资产
├── audio/
│   ├── bgm/                       # 背景音乐
│   ├── sfx/                       # 音效
│   └── voice/                     # 配音文件
├── video/
│   ├── raw/                       # Seedance原始输出
│   └── edited/                    # 剪辑后
└── final/                         # 最终成片
```

### 5.3 项目数据持久化

```python
def save_project(self, project: Project):
    """
    将项目保存为JSON文件
    """
    project.updated_at = datetime.now().isoformat()
    path = Path(project.output_dir) / "project_2026.json"
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)
```

保存的JSON示例：
```json
{
  "name": "我的短剧",
  "video_backend": "seedance-2.0",
  "resolution": "2k",
  "characters": [
    {
      "name": "女主",
      "reference_images": ["face1.jpg", "face2.jpg"],
      "trigger_word": "FemaleLead"
    }
  ],
  "scenes": [
    {
      "scene_id": "scene_001",
      "title": "初次相遇",
      "shots": [
        {
          "shot_id": "scene_001_shot_001",
          "description": "女主特写",
          "generation_prompt": "自动生成的提示词...",
          "status": "generated",
          "output_video": "video/raw/scene_001_shot_001.mp4"
        }
      ]
    }
  ]
}
```

---

## 六、完整工作流程

### 6.1 从0到成片的完整流程

```
第1步：创建项目
─────────────────
pm = PipelineManager2026()
project = pm.create_project(
    name="咖啡店老板",
    genre="romance",
    resolution="2k"
)

        ↓

第2步：添加角色（关键！决定一致性）
─────────────────
pm.add_character(
    name="咖啡店老板",
    description="30岁男性，温柔",
    reference_images=[
        "characters/reference_images/boss_01.jpg",
        "characters/reference_images/boss_02.jpg",
        "characters/reference_images/boss_03.jpg"
    ]
)
# 把照片放进 reference_images/ 文件夹

        ↓

第3步：创建场景
─────────────────
scene = pm.add_scene(
    title="清晨开店",
    description="老板打开咖啡店门",
    location="cozy coffee shop",
    time_of_day="morning",
    mood="peaceful"
)
# 自动创建 scenes/scene_001/ 目录

        ↓

第4步：添加镜头
─────────────────
pm.add_shot(
    scene_id="scene_001",
    description="老板开门的全景",
    shot_type="wide",
    camera_move="static",
    characters=["咖啡店老板"],
    duration=8
)
# 自动生成 generation_prompt

pm.add_shot(
    scene_id="scene_001",
    description="老板微笑特写",
    shot_type="closeup",
    camera_move="slow_zoom_in",
    characters=["咖啡店老板"],
    dialogue="欢迎光临",
    duration=5
)

        ↓

第5步：设置API密钥
─────────────────
pm.set_api_key("your-seedance-api-key")

        ↓

第6步：生成视频
─────────────────
pm.generate_scene("scene_001")

内部流程：
1. 遍历 scene_001 的所有 shots
2. 对每个 shot:
   a. 收集角色参考图
   b. SeedancePromptEngineer 生成提示词
   c. SeedanceAPI.generate_video() 调用API
   d. 下载视频到 video/raw/
   e. 更新 shot.status = "generated"
   f. 保存 project_2026.json

        ↓

第7步：检查和迭代
─────────────────
# 查看生成结果
for shot in scene.shots:
    print(f"{shot.shot_id}: {shot.output_video}")

# 如果不满意，修改参数重新生成
# 或调整 prompt 再次调用 generate_shot()

        ↓

第8步：后期制作（可选）
─────────────────
# 使用视频编辑软件
# - 导入 video/raw/ 下的所有片段
# - 添加转场
# - 调整色彩
# - 导出到 final/
```

---

## 七、实际使用示例

### 7.1 最小可用示例

```python
# 1. 导入
from ai_drama_pipeline_2026 import PipelineManager2026

# 2. 创建管理器
pm = PipelineManager2026()

# 3. 创建项目
project = pm.create_project("测试项目")

# 4. 添加角色（准备3张参考图）
pm.add_character(
    name="测试角色",
    reference_images=["test1.jpg", "test2.jpg", "test3.jpg"]
)

# 5. 添加场景
scene = pm.add_scene(
    title="测试场景",
    location="park"
)

# 6. 添加镜头
pm.add_shot(
    scene_id=scene.scene_id,
    description="角色站在公园里",
    shot_type="medium",
    characters=["测试角色"]
)

# 7. 设置API密钥（需要申请）
pm.set_api_key("your-api-key-here")

# 8. 生成
result = pm.generate_scene(scene.scene_id)
print(f"生成完成: {result}")
```

### 7.2 查看生成的提示词

```python
# 查看某个镜头的自动生成提示词
shot = pm.current_project.scenes[0].shots[0]
print("正提示词:", shot.generation_prompt)
print("负提示词:", shot.negative_prompt)

# 手动修改后重新生成
shot.generation_prompt += ", golden hour lighting"
pm.save_project(pm.current_project)
pm.generate_shot(shot.shot_id)
```

### 7.3 导出配置给其他工具

```python
# 导出为Seedance批量配置
config = pm.export_seedance_config()
# 保存为JSON，可以在其他脚本中使用

with open("seedance_batch_config.json", "w") as f:
    json.dump(config, f, indent=2)
```

---

## 八、常见问题

### Q1: reference_images 应该放什么照片？

**推荐组合（最多9张）**:
- 必传（3张）: 正面、侧面、45度角
- 表情（2张）: 微笑、严肃
- 动作（2张）: 站立、行走
- 服装（2张）: 不同服装

### Q2: 如何保持多个镜头角色一致？

**Pipeline自动处理**:
1. 同一角色的所有镜头使用相同的 reference_images
2. Seedance 2.0 会自动锁定这些特征
3. 不需要像2024年那样训练LoRA

### Q3: 生成的视频在哪里？

**默认位置**:
```
ai_drama_projects/{项目名称}/
└── video/
    └── raw/
        ├── scene_001_shot_001.mp4
        ├── scene_001_shot_002.mp4
        └── ...
```

路径也会保存在 `project_2026.json` 中。

### Q4: 如何修改已经生成的镜头？

```python
# 找到shot
for scene in pm.current_project.scenes:
    for shot in scene.shots:
        if shot.shot_id == "scene_001_shot_001":
            # 修改参数
            shot.duration = 10  # 改时长
            shot.camera_move = "zoom_in"  # 改运镜
            
            # 重新生成提示词
            engineer = SeedancePromptEngineer(pm.current_project)
            shot.generation_prompt = engineer.generate_shot_prompt(
                shot, scene
            )
            
            # 重新生成
            pm.generate_shot(shot.shot_id)
```

---

## 九、下一步扩展方向

1. **质量控制模块** - 自动分析生成视频的问题
2. **迭代优化器** - 根据反馈自动调整prompt
3. **批量生成队列** - 管理大量生成任务
4. **视频后期自动化** - 自动剪辑、调色
5. **多平台导出** - 一键导出到抖音/YouTube/Instagram格式

---

**现在你应该理解了整个Pipeline的工作原理。有什么具体问题想深入讨论吗？**
