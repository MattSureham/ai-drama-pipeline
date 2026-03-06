# 🔑 如何获取 Seedance 2.0 API 访问权限

本文档汇总所有已知的Seedance 2.0 API获取渠道（截至2026年3月）。

---

## ⚠️ 重要说明

**Seedance 2.0官方API状态**：ByteDance尚未全面开放官方直接API申请。目前主要通过以下方式访问：

1. **第三方API聚合平台**（推荐，立即可用）
2. **ByteDance官方产品**（需等待/邀请码）
3. **开源/社区集成**（技术门槛较高）

---

## 方法一：第三方API平台（推荐 ⭐）

这些平台已经对接了Seedance 2.0，提供统一API接口。

### 1. PiAPI (https://piapi.ai/seedance-2-0)

| 项目 | 详情 |
|------|------|
| **网址** | https://piapi.ai/seedance-2-0 |
| **接入方式** | REST API |
| **特点** | 专门针对Seedance 2.0优化，有免费试用 |
| **价格** | 按量付费，有免费额度 |
| **难度** | ⭐ 简单 |

**接入步骤**：
```bash
# 1. 注册账号
https://piapi.ai/signup

# 2. 获取API Key
Dashboard -> API Keys -> Create New Key

# 3. 调用示例
curl -X POST https://api.piapi.ai/v1/seedance \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "seedance-2.0-pro",
    "prompt": "cinematic shot...",
    "reference_images": ["data:image/jpeg;base64,..."],
    "duration": 10,
    "resolution": "2k"
  }'
```

**Python SDK**：
```python
from piapi import SeedanceClient

client = SeedanceClient(api_key="your-key")
video_url = client.generate(
    prompt="cinematic shot...",
    reference_images=["char1.jpg", "char2.jpg"],
    duration=10
)
```

### 2. Atlas Cloud (https://www.atlascloud.ai)

| 项目 | 详情 |
|------|------|
| **网址** | https://www.atlascloud.ai |
| **特点** | 统一API接入多个模型（Seedance/Sora/Runway等） |
| **免费额度** | 新用户有免费额度 |
| **价格** | Pay-as-you-go |
| **难度** | ⭐ 简单 |

**接入步骤**：
```bash
# 1. 注册
https://www.atlascloud.ai/signup

# 2. 创建API Key
Settings -> API Keys

# 3. 调用
curl -X POST https://api.atlascloud.ai/v1/video/generate \
  -H "Authorization: Bearer YOUR_KEY" \
  -d '{
    "model": "bytedance/seedance-2.0-pro",
    "prompt": "your prompt",
    "reference_images": [...]
  }'
```

### 3. APIYI (https://apiyi.com)

| 项目 | 详情 |
|------|------|
| **网址** | https://apiyi.com |
| **特点** | 中文友好，支持批量生成 |
| **文档** | https://help.apiyi.com/en/seedance-2-api-video-generation-guide-en.html |
| **难度** | ⭐⭐ 中等（中文文档） |

---

## 方法二：ByteDance官方渠道

### 1. Dreamina (剪映国际版)

| 项目 | 详情 |
|------|------|
| **网址** | https://dreamina.capcut.com |
| **类型** | Web界面 + 部分API |
| **特点** | ByteDance官方国际版，最稳定 |
| **限制** | 主要是Web界面，API能力有限 |
| **难度** | ⭐ 简单（Web）/ ⭐⭐⭐ 难（API） |

**访问方式**：
1. 访问 https://dreamina.capcut.com
2. 注册/登录账号
3. 在Web界面使用Seedance 2.0
4. API访问需申请开发者权限（见下文）

### 2. CapCut App

| 项目 | 详情 |
|------|------|
| **平台** | iOS / Android / Desktop |
| **类型** | 移动端App |
| **特点** | 10亿+用户基础，功能最全 |
| **限制** | 无直接API，只能手动操作 |
| **难度** | ⭐ 简单 |

**使用方式**：
1. 下载CapCut App
2. 登录账号
3. 在AI功能中找到Seedance 2.0
4. 适合：个人创作，不适合批量自动化

### 3. 官方API申请（开发者）

| 项目 | 详情 |
|------|------|
| **网址** | https://seed.bytedance.com/en/seedance2_0 |
| **类型** | 官方直接API |
| **状态** | 需要申请，审核较严 |
| **难度** | ⭐⭐⭐⭐ 很难 |

**申请步骤**：
```
1. 访问 https://seed.bytedance.com/en/seedance2_0
2. 点击 "Contact Us" 或 "Join Us"（在页面底部）
3. 填写申请表，包括：
   - 公司/个人身份
   - 使用场景
   - 预计调用量
   - 技术团队规模
4. 等待审核（通常2-4周）
5. 审核通过后获得API Key
```

**申请模板**：
```
Subject: Seedance 2.0 API Access Application

Dear ByteDance Seed Team,

I am applying for Seedance 2.0 API access for creative video production.

Company/Individual: [Your Name/Company]
Use Case: AI short drama production pipeline
Expected Volume: ~100 videos/month
Technical Setup: Python backend, automated pipeline
Previous Experience: [Any relevant AI/video experience]

We plan to use Seedance 2.0 for:
- Character-consistent storytelling
- Multi-modal video generation
- Automated short drama production

Please consider our application.

Best regards,
[Your Name]
```

---

## 方法三：Beta测试/邀请码

### Chatcut Beta (需邀请码)

| 项目 | 详情 |
|------|------|
| **网址** | https://chatcut.com |
| **类型** | Beta测试 |
| **要求** | 需要邀请码 |
| **难度** | ⭐⭐ 中等（需找邀请码） |

**获取邀请码方式**：
1. 关注ByteDance官方社交媒体账号
2. 加入相关Discord/Telegram群组
3. 在Reddit r/generativeAI板块询问
4. 一些科技博主会分享邀请码

**常见邀请码尝试**（可能已过期，需自行验证）：
- `SEEDANCE2026`
- `BYTEBRIDGE`
- `AIVIDEO2026`

---

## 方法四：开源/社区方案

### ComfyUI集成

| 项目 | 详情 |
|------|------|
| **类型** | 开源工具 |
| **GitHub** | 搜索 "ComfyUI Seedance" |
| **特点** | 本地运行，无需API Key |
| **难度** | ⭐⭐⭐⭐ 技术门槛高 |
| **要求** | 需要GPU，技术能力强 |

**注意**：社区集成可能不稳定，功能不完整。适合研究，不适合生产环境。

---

## 📊 方案对比

| 方案 | 难度 | 成本 | 稳定性 | 适用场景 |
|------|------|------|--------|---------|
| **PiAPI** | ⭐ 低 | 按量付费 | ⭐⭐⭐⭐ 高 | 生产环境 |
| **Atlas Cloud** | ⭐ 低 | 免费额度+付费 | ⭐⭐⭐⭐ 高 | 生产环境 |
| **Dreamina Web** | ⭐ 低 | 免费/订阅 | ⭐⭐⭐⭐⭐ 最高 | 个人创作 |
| **官方API申请** | ⭐⭐⭐⭐ 高 | 企业定价 | ⭐⭐⭐⭐⭐ 最高 | 大规模生产 |
| **Beta邀请码** | ⭐⭐ 中 | 免费 | ⭐⭐⭐ 中等 | 测试/尝鲜 |
| **ComfyUI开源** | ⭐⭐⭐⭐ 高 | 免费（需GPU） | ⭐⭐ 低 | 研究/学习 |

---

## 🚀 推荐路径

### 场景1：快速测试（今天就想用）
```
PiAPI 或 Atlas Cloud → 注册 → 获取API Key → 开始生成
时间：5分钟
成本：免费额度足够测试
```

### 场景2：正式项目（需要稳定服务）
```
1. 先用 PiAPI/Atlas Cloud 开发原型
2. 同时申请 ByteDance 官方API
3. 官方通过后再迁移
时间：开发1周 + 官方审核2-4周
```

### 场景3：个人创作者（不编程）
```
Dreamina Web 或 CapCut App
直接使用Web界面，无需API
```

---

## 🔧 在Pipeline中使用

以PiAPI为例，修改我们的代码：

```python
# ai_drama_pipeline_2026.py 中修改 SeedanceAPI 类

class SeedanceAPI:
    # 改为第三方API端点
    API_ENDPOINT = "https://api.piapi.ai/v1/seedance"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_video(self, prompt, reference_images, ...):
        payload = {
            "model": "seedance-2.0-pro",
            "prompt": prompt,
            "reference_images": self._encode_images(reference_images),
            "duration": duration,
            "resolution": resolution
        }
        
        response = requests.post(self.API_ENDPOINT, 
                                headers=self.headers, 
                                json=payload)
        return response.json()
    
    def _encode_images(self, image_paths):
        """将图片转为base64"""
        import base64
        encoded = []
        for path in image_paths:
            with open(path, "rb") as f:
                encoded.append(base64.b64encode(f.read()).decode())
        return encoded
```

---

## ⚠️ 常见问题

### Q1: 第三方平台安全吗？

**A**: PiAPI和Atlas Cloud都是知名AI API聚合平台，有一定信誉。但：
- 不要在第三方平台存储敏感信息
- 使用限额度的API Key
- 生产环境建议使用官方API（如果能申请到）

### Q2: 价格如何？

**A**（大致价格，以实际为准）：
```
PiAPI: ~$0.05-0.10 / 秒视频
Atlas Cloud: ~$0.08-0.15 / 秒视频
官方API: 企业定价，需询价
```

### Q3: 有免费额度吗？

**A**: 
- PiAPI: 新用户有$5-10免费额度
- Atlas Cloud: 新用户有免费试用额度
- Dreamina Web: 每日免费生成次数限制

### Q4: 中国用户可以访问吗？

**A**: 
- PiAPI/Atlas Cloud: 全球可用
- Dreamina: 国际版，部分地区可能受限
- 官方API: 企业用户通常无地域限制

---

## 📞 获取更多帮助

| 渠道 | 链接 |
|------|------|
| PiAPI Discord | https://discord.gg/piapi |
| Atlas Cloud Docs | https://docs.atlascloud.ai |
| Reddit讨论 | https://reddit.com/r/generativeAI |
| ByteDance官方 | seed@bytedance.com |

---

**推荐下一步**：
1. 先去 https://piapi.ai 注册，5分钟拿到API Key
2. 用我们的Pipeline测试生成第一个视频
3. 同时申请ByteDance官方API（长期方案）
