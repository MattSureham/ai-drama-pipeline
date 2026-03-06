#!/usr/bin/env python3
"""
AI Short Drama Pipeline - 自动化AI短剧制作工作流

功能：
1. 项目管理（场景/镜头/资产追踪）
2. 提示词自动生成与优化
3. 批量图像生成调度
4. 角色一致性检查
5. 视频生成任务队列
"""

import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import random


@dataclass
class Character:
    """角色资产"""
    name: str
    description: str
    lora_path: Optional[str] = None
    reference_images: List[str] = None
    trigger_word: str = ""
    attributes: Dict = None  # age, hair_color, clothing_style, etc.
    
    def __post_init__(self):
        if self.reference_images is None:
            self.reference_images = []
        if self.attributes is None:
            self.attributes = {}
        if not self.trigger_word:
            self.trigger_word = self.name.replace(" ", "")


@dataclass
class Shot:
    """单个镜头"""
    shot_id: str
    scene_id: str
    description: str
    shot_type: str  # wide, medium, closeup, extreme_closeup
    characters: List[str]
    location: str
    action: str
    emotion: str
    prompt: str = ""
    negative_prompt: str = ""
    reference_image: Optional[str] = None
    generated_images: List[str] = None
    selected_image: Optional[str] = None
    video_clip: Optional[str] = None
    status: str = "pending"  # pending, generated, selected, animated, completed
    
    def __post_init__(self):
        if self.generated_images is None:
            self.generated_images = []


@dataclass
class Scene:
    """场景（包含多个镜头）"""
    scene_id: str
    scene_number: int
    title: str
    description: str
    location: str
    time_of_day: str
    mood: str
    shots: List[Shot] = None
    
    def __post_init__(self):
        if self.shots is None:
            self.shots = []


@dataclass
class Project:
    """短剧项目"""
    name: str
    created_at: str
    updated_at: str
    genre: str  # drama, comedy, scifi, romance, etc.
    style: str  # realistic, anime, cinematic, etc.
    characters: List[Character]
    scenes: List[Scene]
    base_prompt: str = ""
    negative_prompt: str = ""
    output_dir: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Project':
        characters = [Character(**c) for c in data.get('characters', [])]
        scenes = []
        for s in data.get('scenes', []):
            shots = [Shot(**sh) for sh in s.get('shots', [])]
            scene_data = {k: v for k, v in s.items() if k != 'shots'}
            scene_data['shots'] = shots
            scenes.append(Scene(**scene_data))
        
        data['characters'] = characters
        data['scenes'] = scenes
        return cls(**data)


class PromptEngineer:
    """提示词工程师 - 自动生成优化提示词"""
    
    # 质量增强词
    QUALITY_TAGS = [
        "masterpiece", "best quality", "highly detailed", "8k resolution",
        "cinematic lighting", "professional photography", "film grain",
        "sharp focus", "vivid colors", "dynamic composition"
    ]
    
    # 镜头类型定义
    SHOT_TYPES = {
        "wide": "wide shot, full body, establishing shot, scenic background",
        "medium": "medium shot, waist up, balanced composition",
        "closeup": "close-up shot, head and shoulders, emotional",
        "extreme_closeup": "extreme close-up, facial details, intense emotion",
        "over_shoulder": "over the shoulder shot, conversation",
        "POV": "point of view shot, first person perspective"
    }
    
    # 情绪光照映射
    MOOD_LIGHTING = {
        "happy": "bright, warm lighting, golden hour, soft shadows",
        "sad": "cool tones, overcast, soft diffused light, blue hour",
        "tense": "high contrast, dramatic shadows, chiaroscuro lighting",
        "romantic": "warm glow, sunset, bokeh background, soft focus",
        "mysterious": "low key lighting, fog, silhouettes, rim lighting",
        "scary": "harsh shadows, red tones, darkness, flashlight"
    }
    
    def __init__(self, project: Project):
        self.project = project
    
    def generate_shot_prompt(self, shot: Shot, scene_time_of_day: str = "day") -> Tuple[str, str]:
        """为镜头生成完整的正负提示词"""
        
        # 基础质量词
        quality = ", ".join(random.sample(self.QUALITY_TAGS, 4))
        
        # 角色描述
        character_descs = []
        for char_name in shot.characters:
            char = self._get_character(char_name)
            if char:
                desc = f"({char.trigger_word}:1.2)"  # 加权触发词
                if char.attributes:
                    attrs = ", ".join([f"{k} {v}" for k, v in char.attributes.items()])
                    desc += f", {attrs}"
                character_descs.append(desc)
        
        characters = ", ".join(character_descs) if character_descs else "person"
        
        # 镜头类型
        shot_type_desc = self.SHOT_TYPES.get(shot.shot_type, "medium shot")
        
        # 光照/情绪
        mood_light = self.MOOD_LIGHTING.get(shot.emotion, "natural lighting")
        
        # 场景环境
        location_desc = f"in {shot.location}, {shot.action}"
        
        # 时间和天气
        time_desc = self._get_time_description(scene_time_of_day)
        
        # 组合正提示词
        positive = f"{quality}, {shot_type_desc}, {characters}, {location_desc}, {mood_light}, {time_desc}, {self.project.style}"
        
        # 负提示词
        negative = self._generate_negative_prompt()
        
        return positive, negative
    
    def _get_character(self, name: str) -> Optional[Character]:
        for char in self.project.characters:
            if char.name == name:
                return char
        return None
    
    def _get_time_description(self, time_of_day: str) -> str:
        """根据场景时间生成描述"""
        time_map = {
            "morning": "morning light, soft shadows",
            "noon": "bright daylight, harsh shadows",
            "afternoon": "golden hour, warm tones",
            "evening": "sunset, orange sky",
            "night": "night time, artificial lighting, city lights",
            "dawn": "blue hour, misty, pre-dawn"
        }
        return time_map.get(time_of_day, "daytime")
    
    def _generate_negative_prompt(self) -> str:
        """生成负提示词"""
        negatives = [
            "bad anatomy", "extra limbs", "missing fingers",
            "blurry", "low quality", "watermark", "signature",
            "deformed", "ugly", "duplicate", "morbid",
            "mutated hands", "poorly drawn hands", "poorly drawn face",
            "mutation", "deformed", "extra fingers", "fused fingers",
            "too many fingers", "long neck", "cross-eyed",
            "mutated hands", "polar lowres", "bad hands",
            "bad body", "bad proportions", "gross proportions",
            "text", "error", "missing arms", "missing legs",
            "extra arms", "extra legs", "cropped", "worst quality",
            "low resolution", "normal quality", "username"
        ]
        return ", ".join(negatives)
    
    def optimize_for_model(self, prompt: str, model: str) -> str:
        """针对特定模型优化提示词"""
        optimizations = {
            "midjourney": lambda p: p.replace("(", "{").replace(")", "}").replace(":", "="),
            "sdxl": lambda p: p,  # SDXL原生支持加权
            "flux": lambda p: p.replace("masterpiece, best quality", "").strip(),  # FLUX不需要这些
            "dalle3": lambda p: p.replace("(", "").replace(")", "").replace(":1.2", "")  # DALL-E不支持加权
        }
        
        optimizer = optimizations.get(model.lower(), lambda p: p)
        return optimizer(prompt)


class PipelineManager:
    """Pipeline管理器 - 项目全流程管理"""
    
    def __init__(self, project_dir: str = "ai_drama_projects"):
        self.project_dir = Path(project_dir)
        self.project_dir.mkdir(exist_ok=True)
        self.current_project: Optional[Project] = None
    
    def create_project(self, name: str, genre: str = "drama", style: str = "cinematic") -> Project:
        """创建新项目"""
        now = datetime.now().isoformat()
        project = Project(
            name=name,
            created_at=now,
            updated_at=now,
            genre=genre,
            style=style,
            characters=[],
            scenes=[],
            output_dir=str(self.project_dir / name)
        )
        
        # 创建目录结构
        self._create_project_structure(project)
        self.current_project = project
        return project
    
    def _create_project_structure(self, project: Project):
        """创建项目目录结构"""
        base = Path(project.output_dir)
        dirs = [
            "characters/lora_training",
            "characters/reference",
            "scenes",  # 场景文件夹会自动创建
            "audio/voice",
            "audio/music",
            "audio/sfx",
            "video/raw",
            "video/edited",
            "final",
            "scripts"
        ]
        
        for d in dirs:
            (base / d).mkdir(parents=True, exist_ok=True)
        
        # 保存项目文件
        self.save_project(project)
    
    def save_project(self, project: Project):
        """保存项目到JSON"""
        project.updated_at = datetime.now().isoformat()
        path = Path(project.output_dir) / "project.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)
    
    def load_project(self, name: str) -> Optional[Project]:
        """加载项目"""
        path = self.project_dir / name / "project.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.current_project = Project.from_dict(data)
            return self.current_project
        return None
    
    def add_character(self, name: str, description: str, **kwargs) -> Character:
        """添加角色"""
        char = Character(name=name, description=description, **kwargs)
        self.current_project.characters.append(char)
        self.save_project(self.current_project)
        return char
    
    def add_scene(self, title: str, description: str, location: str, 
                  time_of_day: str = "day", mood: str = "neutral") -> Scene:
        """添加场景"""
        scene_num = len(self.current_project.scenes) + 1
        scene_id = f"scene_{scene_num:03d}"
        
        scene = Scene(
            scene_id=scene_id,
            scene_number=scene_num,
            title=title,
            description=description,
            location=location,
            time_of_day=time_of_day,
            mood=mood
        )
        
        # 创建场景目录
        scene_dir = Path(self.current_project.output_dir) / "scenes" / scene_id
        scene_dir.mkdir(exist_ok=True)
        (scene_dir / "shots").mkdir(exist_ok=True)
        
        self.current_project.scenes.append(scene)
        self.save_project(self.current_project)
        return scene
    
    def add_shot(self, scene_id: str, description: str, shot_type: str = "medium",
                 characters: List[str] = None, action: str = "", emotion: str = "neutral") -> Shot:
        """添加镜头到场景"""
        scene = self._get_scene(scene_id)
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        shot_num = len(scene.shots) + 1
        shot_id = f"{scene_id}_shot_{shot_num:03d}"
        
        shot = Shot(
            shot_id=shot_id,
            scene_id=scene_id,
            description=description,
            shot_type=shot_type,
            characters=characters or [],
            location=scene.location,
            action=action,
            emotion=emotion
        )
        
        # 自动生成提示词
        engineer = PromptEngineer(self.current_project)
        shot.prompt, shot.negative_prompt = engineer.generate_shot_prompt(shot, scene.time_of_day)
        
        scene.shots.append(shot)
        self.save_project(self.current_project)
        return shot
    
    def _get_scene(self, scene_id: str) -> Optional[Scene]:
        for scene in self.current_project.scenes:
            if scene.scene_id == scene_id:
                return scene
        return None
    
    def generate_batch_prompts(self, scene_id: Optional[str] = None) -> List[Dict]:
        """批量生成所有镜头的提示词"""
        prompts = []
        engineer = PromptEngineer(self.current_project)
        
        scenes = [self._get_scene(scene_id)] if scene_id else self.current_project.scenes
        
        for scene in scenes:
            if not scene:
                continue
            for shot in scene.shots:
                if shot.status == "pending":
                    pos, neg = engineer.generate_shot_prompt(shot, scene.time_of_day)
                    prompts.append({
                        "shot_id": shot.shot_id,
                        "scene_id": scene.scene_id,
                        "positive": pos,
                        "negative": neg,
                        "shot_type": shot.shot_type,
                        "characters": shot.characters
                    })
        
        return prompts
    
    def export_for_comfyui(self, output_path: str = None):
        """导出为ComfyUI可用的批量提示词文件"""
        if output_path is None:
            output_path = Path(self.current_project.output_dir) / "comfyui_prompts.json"
        
        prompts = self.generate_batch_prompts()
        
        # 添加ComfyUI特定配置
        comfy_config = {
            "project_name": self.current_project.name,
            "base_model": "SDXL",
            "lora_folder": "characters/lora_training",
            "ip_adapter_enabled": True,
            "controlnet_enabled": True,
            "shots": prompts
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(comfy_config, f, ensure_ascii=False, indent=2)
        
        return output_path
    
    def get_progress(self) -> Dict:
        """获取项目进度"""
        total_shots = 0
        completed_shots = 0
        status_counts = {"pending": 0, "generated": 0, "selected": 0, "animated": 0, "completed": 0}
        
        for scene in self.current_project.scenes:
            for shot in scene.shots:
                total_shots += 1
                status_counts[shot.status] = status_counts.get(shot.status, 0) + 1
                if shot.status == "completed":
                    completed_shots += 1
        
        return {
            "total_scenes": len(self.current_project.scenes),
            "total_shots": total_shots,
            "completed_shots": completed_shots,
            "progress_percentage": (completed_shots / total_shots * 100) if total_shots > 0 else 0,
            "status_breakdown": status_counts
        }


class WorkflowTemplates:
    """预设工作流模板"""
    
    @staticmethod
    def romance_drama(title: str = "都市爱情") -> Project:
        """浪漫爱情剧模板"""
        pm = PipelineManager()
        project = pm.create_project(title, genre="romance", style="cinematic, soft lighting")
        
        # 添加典型角色
        pm.add_character(
            name="女主角",
            description="25岁职场女性，长发，知性优雅",
            attributes={"age": "25", "hair": "long black hair", "style": "professional, elegant"},
            trigger_word="FemaleLead"
        )
        pm.add_character(
            name="男主角",
            description="28岁精英男性，短发，帅气沉稳",
            attributes={"age": "28", "hair": "short black hair", "style": "business casual, confident"},
            trigger_word="MaleLead"
        )
        
        return project
    
    @staticmethod
    def scifi_short(title: str = "科幻短片") -> Project:
        """科幻短片模板"""
        pm = PipelineManager()
        project = pm.create_project(title, genre="scifi", style="cyberpunk, neon lights, futuristic")
        
        pm.add_character(
            name="赛博主角",
            description="改造人，机械义肢，未来感服装",
            attributes={"style": "cyberpunk, neon accents, techwear", "features": "glowing eyes"},
            trigger_word="CyberProtagonist"
        )
        
        return project
    
    @staticmethod
    def period_drama(title: str = "古装短剧") -> Project:
        """古装短剧模板"""
        pm = PipelineManager()
        project = pm.create_project(title, genre="period", style="historical, traditional costume, cinematic")
        
        pm.add_character(
            name="古代女主",
            description="古代贵族女子，汉服，精致妆容",
            attributes={"clothing": "hanfu, flowing robes", "hairstyle": "traditional updo, hair ornaments"},
            trigger_word="AncientLady"
        )
        
        return project


def demo():
    """演示如何使���Pipeline"""
    print("=" * 60)
    print("🎬 AI短剧 Pipeline 演示")
    print("=" * 60)
    
    # 1. 创建项目
    pm = PipelineManager()
    project = pm.create_project(
        name="咖啡店邂逅",
        genre="romance",
        style="cinematic, warm lighting, film grain"
    )
    print(f"\n✅ 创建项目: {project.name}")
    
    # 2. 添加角色
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
        trigger_word="XiaoYa"
    )
    
    pm.add_character(
        name="阿杰",
        description="28岁程序员，戴眼镜，内敛温暖",
        attributes={
            "age": "28",
            "hair": "black hair",
            "glasses": "round glasses",
            "style": "minimalist, hoodie, casual",
            "personality": "shy, kind, intelligent"
        },
        trigger_word="AJie"
    )
    print("✅ 添加角色: 小雅, 阿杰")
    
    # 3. 添加场景
    scene1 = pm.add_scene(
        title="初次相遇",
        description="小雅在咖啡店画画，不小心打翻咖啡",
        location="cozy coffee shop",
        time_of_day="afternoon",
        mood="romantic"
    )
    print(f"✅ 添加场景: {scene1.title}")
    
    # 4. 添加镜头
    shot1 = pm.add_shot(
        scene_id=scene1.scene_id,
        description="小雅专注画画的中景",
        shot_type="medium",
        characters=["小雅"],
        action="sitting by window, sketching in notebook",
        emotion="peaceful"
    )
    
    shot2 = pm.add_shot(
        scene_id=scene1.scene_id,
        description="阿杰注意到小雅的侧脸特写",
        shot_type="closeup",
        characters=["阿杰"],
        action="looking at XiaoYa from across the room",
        emotion="curious"
    )
    
    shot3 = pm.add_shot(
        scene_id=scene1.scene_id,
        description="小雅打翻咖啡，表情惊讶",
        shot_type="medium",
        characters=["小雅"],
        action="knocking over coffee cup, surprised expression",
        emotion="surprised"
    )
    
    print(f"✅ 添加 {len(scene1.shots)} 个镜头")
    
    # 5. 显示生成的提示词
    print("\n" + "=" * 60)
    print("📝 自动生成的提示词示例:")
    print("=" * 60)
    
    for shot in scene1.shots[:2]:  # 显示前2个
        print(f"\n镜头 {shot.shot_id}:")
        print(f"  描述: {shot.description}")
        print(f"  正提示词: {shot.prompt[:100]}...")
        print(f"  负提示词: {shot.negative_prompt[:80]}...")
    
    # 6. 导出ComfyUI配置
    export_path = pm.export_for_comfyui()
    print(f"\n✅ 导出ComfyUI配置: {export_path}")
    
    # 7. 查看进度
    progress = pm.get_progress()
    print(f"\n📊 项目进度:")
    print(f"  场景数: {progress['total_scenes']}")
    print(f"  总镜头: {progress['total_shots']}")
    print(f"  完成度: {progress['progress_percentage']:.1f}%")
    
    # 8. 显示批量提示词
    print("\n" + "=" * 60)
    print("📋 批量生成任务列表:")
    print("=" * 60)
    
    batch = pm.generate_batch_prompts()
    for item in batch[:3]:
        print(f"\n{item['shot_id']}:")
        print(f"  角色: {', '.join(item['characters'])}")
        print(f"  镜头: {item['shot_type']}")
    
    print(f"\n总计 {len(batch)} 个待生成镜头")
    print("\n" + "=" * 60)
    print("✨ 演示完成！查看项目文件夹了解详细结构")
    print("=" * 60)
    
    return pm


if __name__ == "__main__":
    demo()
