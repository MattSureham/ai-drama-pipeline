# 🎬 AI Drama Pipeline

AI短剧制作Pipeline工具集 - 支持Seedance 2.0、ComfyUI等多种工作流

> **Context Checkpoint**: 这个仓库是我们长期对话的知识锚点。当对话上下文达到限制时，可以通过这个仓库回顾之前的讨论和代码。

---

## 📦 仓库内容

| 文件 | 说明 | 状态 |
|------|------|------|
| `ai_drama_pipeline_2026.py` | **Seedance 2.0版** - ByteDance多模态视频生成 | ✅ 推荐新项目 |
| `ai_drama_pipeline.py` | **2024经典版** - LoRA + ComfyUI方案 | ✅ 稳定可用 |
| `comfyui_workflow_generator.py` | ComfyUI批量工作流JSON生成器 | ✅ 配套工具 |
| `AI_DRAMA_PIPELINE_README.md` | 完整使用文档 | 📖 必读 |
| `SEEDANCE_2.0_GUIDE.md` | Seedance 2.0快速上手指南 | 🚀 快速开始 |
| `HOW_IT_WORKS.md` | **工作原理详解** - 架构、流程、示例 | 🔧 深入理解 |

---

## 🚀 快速开始

### Seedance 2.0 (2026推荐方案)

```python
from ai_drama_pipeline_2026 import PipelineManager2026

pm = PipelineManager2026()
project = pm.create_project("我的短剧", video_backend="seedance-2.0")

# 添加角色（无需LoRA训练！）
pm.add_character(
    name="女主",
    reference_images=["face1.jpg", "face2.jpg", "face3.jpg"]
)

# 添加运镜控制的镜头
pm.add_shot(
    scene_id="scene_001",
    description="女主惊讶特写",
    camera_move="zoom_in",
    dialogue="这怎么可能？"
)

# 生成
pm.set_api_key("your-seedance-api-key")
pm.generate_scene("scene_001")
```

### ComfyUI方案 (2024经典方案)

```python
from ai_drama_pipeline import PipelineManager

pm = PipelineManager()
project = pm.create_project("我的短剧")

# 导出到ComfyUI
pm.export_for_comfyui()  # 生成 comfyui_prompts.json
```

---

## 🎯 核心特性

### Seedance 2.0版 (2026)
- ✅ **多模态输入**: 9图 + 3视频 + 3音频 + 文本
- ✅ **原生音频**: 对白+环境音+音乐同步生成
- ✅ **无需训练**: 参考图直接锁定角色（告别LoRA）
- ✅ **导演级运镜**: 12种运镜 + 6种机位
- ✅ **2K分辨率**: 高质量输出

### 2024经典版
- ✅ **LoRA训练**: 角色一致性保障
- ✅ **ComfyUI集成**: 批量工作流生成
- ✅ **IP-Adapter**: 面部特征锁定
- ✅ **ControlNet**: 姿态控制

---

## 📚 文档索引

| 文档 | 适合人群 | 内容 |
|------|---------|------|
| [🚀 快速开始](SEEDANCE_2.0_GUIDE.md) | 新手 | 5分钟上手Seedance 2.0 |
| [📖 完整文档](AI_DRAMA_PIPELINE_README.md) | 使用者 | 详细API、配置、故障排除 |
| [🔧 工作原理](HOW_IT_WORKS.md) | 开发者 | 架构详解、数据流、扩展指南 |
| [🔑 API获取](API_ACCESS_GUIDE.md) | 所有人 | 如何获取Seedance 2.0 API Key |
| [💬 Issues](../../issues) | 所有人 | 问题反馈、功能讨论 |

---

## 🔄 对话连续性说明

**这个仓库的作用：**

当我们对话达到上下文限制时，可以通过以下方式快速恢复上下文：

1. **查看代码文件** - 回顾之前讨论的工具实现
2. **阅读文档** - 了解之前的决策和设计思路
3. **提交历史** - 通过git log查看迭代过程

**如何参与：**
- 提交Issue讨论新功能
- 提交PR改进代码
- 在Wiki页面补充使用案例

---

## 📝 最新更新

- **2026-03-06**: 创建仓库，添加Seedance 2.0支持
- **2026-03-06**: 添加迭代优化和质量控制模块

---

## 🤝 贡献

欢迎提交Issue和PR！

---

**对话锚点**: 如果你是通过回顾找到这个仓库的，我们的讨论主题是**AI短剧制作的Pipeline工具**，重点包括：
1. Seedance 2.0多模态视频生成
2. 角色一致性保持策略
3. 迭代优化和质量控制
4. ComfyUI工作流自动化

继续对话时，可以从这些文件恢复上下文！
