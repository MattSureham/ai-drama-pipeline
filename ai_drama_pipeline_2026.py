#!/usr/bin/env python3
"""
AI Short Drama Pipeline - Seedance 2.0 Edition (2026)
支持ByteDance Seedance 2.0多模态视频生成
"""

import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import requests


class VideoBackend(Enum):
    """支持的视频生成后端"""
    SEEDANCE_2 = "seedance-2.0"           # ByteDance 多模态原生音频
    RUNWAY_GEN3 = "runway-gen3"           # Runway Gen-3
    LUMA_DREAM = "luma-dream-machine"     # Luma
    KLING_3 = "kling-3.0"                 # 快手可灵
    VEO_3 = "google-veo-3"                # Google Veo


@dataclass
class Character:
    """角色资产 - 2026版支持多参考图"""
    name: str
    description: str
    
    # 2026: 多参考图系统（取代LoRA训练）
    reference_images: List[str] = field(default_factory=list)  # 最多9张
    reference_videos: List[str] = field(default_factory=list)  # 可选：动作参考
    
    trigger_word: str = ""
    attributes: Dict = field(default_factory=dict)
    
    # Seedance 2.0特定
    motion_style: str = "natural"  # natural, dramatic, subtle
    voice_id: Optional[str] = None  # ElevenLabs voice ID
    
    def __post_init__(self):
        if not self.trigger_word:
            self.trigger_word = self.name.replace(" ", "")


@dataclass
class Shot:
    """镜头定义 - 2026版支持多模态输入"""
    shot_id: str
    scene_id: str
    description: str
    
    # 基础设置
    shot_type: str = "medium"  # wide, medium, closeup, extreme_closeup, POV
    characters: List[str] = field(default_factory=list)
    location: str = ""
    action: str = ""
    emotion: str = "neutral"
    
    # 2026: 多模态输入资产
    reference_images: List[str] = field(default_factory=list)   # 关键帧/参考图
    reference_video: Optional[str] = None  # 动作参考视频（最多15s）
    reference_audio: Optional[str] = None  # 音频参考（语调/氛围）
    
    # 运镜控制
    camera_move: str = "static"  # static, pan_left, pan_right, zoom_in, zoom_out, dolly_in, handheld
    camera_angle: str = "eye_level"  # eye_level, low_angle, high_angle, overhead
    
    # 对白/音效
    dialogue: str = ""           # 对白文本（Seedance原生生成语音）
    ambient_sound: str = ""      # 环境音效描述
    music_mood: str = ""         # 背景音乐情绪
    
    # 生成设置
    duration: int = 5            # 秒数（Seedance支持最多15s，建议5-10s/镜头）
    generation_prompt: str = ""  # 自动生成的完整提示词
    status: str = "pending"      # pending, generated, approved
    output_video: Optional[str] = None


@dataclass
class Scene:
    """场景 - 支持多镜头连续生成"""
    scene_id: str
    scene_number: int
    title: str
    description: str
    location: str
    time_of_day: str = "day"
    mood: str = "neutral"
    
    # Seedance 2.0: 一个scene可以一次生成多个镜头
    shots: List[Shot] = field(default_factory=list)
    
    # 场景级别音频
    bg_music_track: Optional[str] = None
    ambient_track: str = "natural"  # 环境音类型
    
    # 生成模式
    generation_mode: str = "batch"  # batch(一起生成) | sequential(逐个生成)


@dataclass
class Project:
    """短剧项目"""
    name: str
    created_at: str
    updated_at: str
    genre: str
    style: str
    
    # 视频生成后端配置
    video_backend: str = "seedance-2.0"
    resolution: str = "1080p"  # 1080p or 2k
    
    characters: List[Character] = field(default_factory=list)
    scenes: List[Scene] = field(default_factory=list)
    
    # Seedance 2.0特定：全局音频风格
    audio_style: str = "cinematic"  # cinematic, documentary, anime, silent_film
    music_genre: str = "orchestral"  # orchestral, electronic, jazz, etc.
    
    output_dir: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SeedancePromptEngineer:
    """Seedance 2.0专用提示词工程师"""
    
    # Seedance 2.0 运镜词汇表
    CAMERA_MOVES = {
        "static": "static camera, fixed frame",
        "pan_left": "smooth pan to the left, revealing scene",
        "pan_right": "smooth pan to the right, revealing scene", 
        "zoom_in": "slow zoom in, focusing on subject",
        "zoom_out": "slow zoom out, revealing wider scene",
        "dolly_in": "dolly in, camera moves closer to subject",
        "dolly_out": "dolly out, camera pulls back",
        "handheld": "subtle handheld camera movement, documentary style",
        "tracking": "tracking shot, follows character movement",
        "crane_up": "crane shot moving upward, epic reveal",
        "crane_down": "crane shot moving down"
    }
    
    CAMERA_ANGLES = {
        "eye_level": "eye level shot, neutral perspective",
        "low_angle": "low angle shot, looking up, powerful perspective",
        "high_angle": "high angle shot, looking down, vulnerable perspective",
        "overhead": "overhead shot, bird's eye view",
        "dutch": "dutch angle, tilted camera, tense atmosphere",
        "worm_eye": "extreme low angle, worm's eye view"
    }
    
    # 音频提示词模板
    AUDIO_TEMPLATES = {
        "romantic": "soft romantic music, gentle piano, warm ambiance",
        "tense": "tense thriller music, low drones, heartbeat rhythm",
        "action": "epic orchestral, fast tempo, percussion heavy",
        "sad": "melancholic strings, minor key, somber atmosphere",
        "happy": "upbeat pop music, bright synths, energetic",
        "mysterious": "ambient electronic, reverberating tones, mysterious"
    }
    
    def __init__(self, project: Project):
        self.project = project
    
    def generate_shot_prompt(self, shot: Shot, scene: Scene) -> str:
        """生成Seedance 2.0优化的提示词"""
        
        # 基础场景描述
        base_desc = f"{shot.action} in {shot.location}, {scene.time_of_day}"
        
        # 角色描述（使用参考图ID，实际API调用时上传）
        char_desc = ""
        for char_name in shot.characters:
            char = self._get_character(char_name)
            if char:
                char_desc += f"character {char.trigger_word} ({char.description}), "
        
        # 运镜描述
        camera_move = self.CAMERA_MOVES.get(shot.camera_move, "static camera")
        camera_angle = self.CAMERA_ANGLES.get(shot.camera_angle, "eye level")
        
        # 光影/情绪
        lighting = self._get_lighting(scene.time_of_day, shot.emotion)
        
        # 组合提示词（Seedance理解自然语言，可以更详细）
        prompt = f"""
Cinematic shot: {shot.shot_type.replace('_', ' ')}, {camera_angle}, {camera_move}.

Scene: {base_desc}. {char_desc}
{lighting}

Technical: {self.project.resolution}, film grain, professional color grading, shallow depth of field.
""".strip()
        
        return prompt
    
    def generate_audio_prompt(self, shot: Shot, scene: Scene) -> str:
        """生成Seedance原生音频提示词"""
        audio_parts = []
        
        # 对白（Seedance可以生成同步语音！）
        if shot.dialogue:
            audio_parts.append(f"character speaking: '{shot.dialogue}'")
        
        # 环境音
        if shot.ambient_sound:
            audio_parts.append(f"ambient: {shot.ambient_sound}")
        elif scene.ambient_track:
            audio_parts.append(f"ambient: {scene.ambient_track}")
        
        # 音乐
        if shot.music_mood:
            music = self.AUDIO_TEMPLATES.get(shot.music_mood, shot.music_mood)
            audio_parts.append(f"background music: {music}")
        elif self.project.music_genre:
            audio_parts.append(f"background music: {self.project.music_genre}")
        
        return "; ".join(audio_parts) if audio_parts else "natural ambient sound"
    
    def _get_character(self, name: str) -> Optional[Character]:
        for char in self.project.characters:
            if char.name == name:
                return char
        return None
    
    def _get_lighting(self, time_of_day: str, emotion: str) -> str:
        """生成光影描述"""
        time_lighting = {
            "morning": "soft morning light, warm golden tones",
            "noon": "bright midday sun, high contrast",
            "afternoon": "golden hour, warm and soft",
            "evening": "sunset glow, orange and purple sky",
            "night": "night lighting, artificial lights, city glow",
            "dawn": "blue hour, cool tones, misty atmosphere"
        }
        
        emotion_lighting = {
            "happy": "bright and vibrant lighting",
            "sad": "muted colors, soft diffused light",
            "tense": "high contrast, dramatic shadows",
            "romantic": "warm glow, soft focus",
            "angry": "harsh lighting, red tones",
            "scared": "low key lighting, deep shadows"
        }
        
        time_desc = time_lighting.get(time_of_day, "natural lighting")
        emotion_desc = emotion_lighting.get(emotion, "")
        
        return f"{time_desc}, {emotion_desc}".strip(", ")


class SeedanceAPI:
    """Seedance 2.0 API封装"""
    
    API_ENDPOINT = "https://api.seedance.ai/v1/generations"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_video(
        self,
        prompt: str,
        reference_images: List[str] = None,  # 最多9张
        reference_videos: List[str] = None,   # 最多3张，每张最多15s
        reference_audios: List[str] = None,   # 最多3张，每张最多15s
        duration: int = 5,                     # 1-15秒
        resolution: str = "1080p",             # 1080p or 2k
        audio_enabled: bool = True
    ) -> Dict:
        """
        调用Seedance 2.0 API生成视频
        
        参考: https://seedance2.ai/docs
        """
        
        payload = {
            "model": "seedance-2.0-pro",
            "prompt": prompt,
            "settings": {
                "resolution": resolution,
                "duration": min(duration, 15),  # 最大15秒
                "audio": audio_enabled,
                "language": "zh" if "中文" in prompt else "en"
            }
        }
        
        # 添加参考资产
        if reference_images:
            payload["reference_images"] = reference_images[:9]
        if reference_videos:
            payload["reference_videos"] = reference_videos[:3]
        if reference_audios:
            payload["reference_audios"] = reference_audios[:3]
        
        try:
            response = requests.post(
                self.API_ENDPOINT,
                headers=self.headers,
                json=payload,
                timeout=300  # 生成可能需要几分钟
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "failed"}
    
    def generate_scene_batch(
        self,
        shots: List[Shot],
        characters: List[Character],
        scene: Scene
    ) -> List[Dict]:
        """
        批量生成一个场景的所有镜头
        Seedance 2.0优势：可以保持角色一致性和音频连贯性
        """
        results = []
        
        # 收集角色参考图
        char_refs = []
        for char in characters:
            char_refs.extend(char.reference_images[:3])  # 每个角色最多3张
        
        for shot in shots:
            # 生成提示词
            engineer = SeedancePromptEngineer(self.project if hasattr(self, 'project') else None)
            video_prompt = engineer.generate_shot_prompt(shot, scene)
            audio_prompt = engineer.generate_audio_prompt(shot, scene)
            
            # 合并提示词（Seedance原生支持音频描述）
            full_prompt = f"{video_prompt}\n\nAudio: {audio_prompt}"
            
            # 调用API
            result = self.generate_video(
                prompt=full_prompt,
                reference_images=char_refs + shot.reference_images,
                reference_videos=[shot.reference_video] if shot.reference_video else None,
                duration=shot.duration,
                audio_enabled=True
            )
            
            results.append({
                "shot_id": shot.shot_id,
                "result": result
            })
        
        return results


class PipelineManager2026:
    """2026版Pipeline管理器 - 原生支持Seedance 2.0"""
    
    def __init__(self, project_dir: str = "ai_drama_projects_2026"):
        self.project_dir = Path(project_dir)
        self.project_dir.mkdir(exist_ok=True)
        self.current_project: Optional[Project] = None
        self.seedance_api: Optional[SeedanceAPI] = None
    
    def set_api_key(self, api_key: str):
        """设置Seedance API密钥"""
        self.seedance_api = SeedanceAPI(api_key)
    
    def create_project(
        self,
        name: str,
        genre: str = "drama",
        style: str = "cinematic",
        video_backend: str = "seedance-2.0",
        resolution: str = "1080p"
    ) -> Project:
        """创建新项目"""
        now = datetime.now().isoformat()
        
        project = Project(
            name=name,
            created_at=now,
            updated_at=now,
            genre=genre,
            style=style,
            video_backend=video_backend,
            resolution=resolution,
            output_dir=str(self.project_dir / name)
        )
        
        self._create_project_structure(project)
        self.current_project = project
        return project
    
    def _create_project_structure(self, project: Project):
        """创建2026版项目目录"""
        base = Path(project.output_dir)
        
        # 标准目录
        dirs = [
            "characters/reference_images",   # 角色参考图（最多9张/角色）
            "characters/reference_videos",   # 角色动作参考
            "characters/voice_clones",       # ElevenLabs voice clones
            "scenes/{scene_id}/shots",
            "scenes/{scene_id}/assets",      # 场景特定资产
            "audio/bgm",
            "audio/sfx",
            "video/raw",                     # Seedance原始输出
            "video/edited",
            "final",
            "exports"                        # 多平台输出
        ]
        
        for d in dirs:
            if "{scene_id}" not in d:
                (base / d).mkdir(parents=True, exist_ok=True)
        
        self.save_project(project)
    
    def add_character(
        self,
        name: str,
        description: str,
        reference_images: List[str] = None,  # 2026: 直接上传参考图
        reference_videos: List[str] = None,
        voice_id: str = None,
        **kwargs
    ) -> Character:
        """添加角色 - 2026版不需要训练LoRA！"""
        
        char = Character(
            name=name,
            description=description,
            reference_images=reference_images or [],
            reference_videos=reference_videos or [],
            voice_id=voice_id,
            **kwargs
        )
        
        self.current_project.characters.append(char)
        self.save_project(self.current_project)
        
        print(f"✅ 添加角色: {name}")
        print(f"   参考图: {len(char.reference_images)}张")
        print(f"   2026优势: 无需训练LoRA，Seedance直接锁定角色特征")
        
        return char
    
    def add_scene(self, title: str, description: str, **kwargs) -> Scene:
        """添加场景"""
        scene_num = len(self.current_project.scenes) + 1
        scene_id = f"scene_{scene_num:03d}"
        
        scene = Scene(
            scene_id=scene_id,
            scene_number=scene_num,
            title=title,
            description=description,
            **kwargs
        )
        
        # 创建场景目录
        scene_dir = Path(self.current_project.output_dir) / "scenes" / scene_id
        scene_dir.mkdir(parents=True, exist_ok=True)
        (scene_dir / "shots").mkdir(exist_ok=True)
        (scene_dir / "assets").mkdir(exist_ok=True)
        
        self.current_project.scenes.append(scene)
        self.save_project(self.current_project)
        return scene
    
    def add_shot(
        self,
        scene_id: str,
        description: str,
        shot_type: str = "medium",
        characters: List[str] = None,
        camera_move: str = "static",
        camera_angle: str = "eye_level",
        dialogue: str = "",
        duration: int = 5,
        **kwargs
    ) -> Shot:
        """添加镜头 - 2026版支持完整运镜控制"""
        
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
            camera_move=camera_move,
            camera_angle=camera_angle,
            dialogue=dialogue,
            duration=duration,
            **kwargs
        )
        
        # 自动生成Seedance优化提示词
        engineer = SeedancePromptEngineer(self.current_project)
        shot.generation_prompt = engineer.generate_shot_prompt(shot, scene)
        
        scene.shots.append(shot)
        self.save_project(self.current_project)
        return shot
    
    def generate_shot(self, shot_id: str, wait: bool = True) -> Dict:
        """
        使用Seedance 2.0生成单个镜头
        2026革命性：原生音频 + 多模态输入
        """
        if not self.seedance_api:
            raise ValueError("请先设置Seedance API密钥: set_api_key()")
        
        # 查找shot
        shot, scene = self._find_shot(shot_id)
        if not shot:
            raise ValueError(f"Shot {shot_id} not found")
        
        print(f"🎬 生成镜头: {shot_id}")
        print(f"   时长: {shot.duration}秒")
        print(f"   运镜: {shot.camera_move} + {shot.camera_angle}")
        
        # 收集角色参考图
        char_refs = []
        for char_name in shot.characters:
            char = self._get_character(char_name)
            if char and char.reference_images:
                char_refs.extend(char.reference_images[:3])
                print(f"   使用角色参考: {char.name} ({len(char.reference_images[:3])}张)")
        
        # 调用Seedance API
        result = self.seedance_api.generate_video(
            prompt=shot.generation_prompt,
            reference_images=char_refs + shot.reference_images,
            reference_videos=[shot.reference_video] if shot.reference_video else None,
            reference_audios=[shot.reference_audio] if shot.reference_audio else None,
            duration=shot.duration,
            resolution=self.current_project.resolution,
            audio_enabled=True  # 2026: 原生音频！
        )
        
        # 更新状态
        if result.get("status") != "failed":
            shot.status = "generated"
            shot.output_video = result.get("video_url")
            self.save_project(self.current_project)
            print(f"✅ 生成成功: {result.get('video_url')}")
        else:
            print(f"❌ 生成失败: {result.get('error')}")
        
        return result
    
    def generate_scene(self, scene_id: str, batch_mode: bool = True) -> List[Dict]:
        """
        生成整个场景的所有镜头
        2026优势：可以保持角色一致性和音频连贯性
        """
        scene = self._get_scene(scene_id)
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        print(f"\n🎬 生成场景: {scene.title}")
        print(f"   镜头数: {len(scene.shots)}")
        print(f"   模式: {'批量生成' if batch_mode else '逐个生成'}")
        
        results = []
        for shot in scene.shots:
            result = self.generate_shot(shot.shot_id)
            results.append(result)
        
        return results
    
    def _get_scene(self, scene_id: str) -> Optional[Scene]:
        for scene in self.current_project.scenes:
            if scene.scene_id == scene_id:
                return scene
        return None
    
    def _get_character(self, name: str) -> Optional[Character]:
        for char in self.current_project.characters:
            if char.name == name:
                return char
        return None
    
    def _find_shot(self, shot_id: str) -> Tuple[Optional[Shot], Optional[Scene]]:
        for scene in self.current_project.scenes:
            for shot in scene.shots:
                if shot.shot_id == shot_id:
                    return shot, scene
        return None, None
    
    def save_project(self, project: Project):
        """保存项目"""
        project.updated_at = datetime.now().isoformat()
        path = Path(project.output_dir) / "project_2026.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)
    
    def load_project(self, name: str) -> Optional[Project]:
        """加载项目"""
        path = self.project_dir / name / "project_2026.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 重建对象...
            self.current_project = Project(**data)
            return self.current_project
        return None
    
    def export_seedance_config(self, scene_id: Optional[str] = None) -> Dict:
        """导出为Seedance 2.0批量配置文件"""
        config = {
            "project": self.current_project.name,
            "backend": "seedance-2.0",
            "resolution": self.current_project.resolution,
            "shots": []
        }
        
        scenes = [self._get_scene(scene_id)] if scene_id else self.current_project.scenes
        
        for scene in scenes:
            if not scene:
                continue
            for shot in scene.shots:
                engineer = SeedancePromptEngineer(self.current_project)
                
                # 收集参考资产
                char_refs = []
                for char_name in shot.characters:
                    char = self._get_character(char_name)
                    if char:
                        char_refs.extend(char.reference_images[:3])
                
                config["shots"].append({
                    "shot_id": shot.shot_id,
                    "prompt": engineer.generate_shot_prompt(shot, scene),
                    "audio_prompt": engineer.generate_audio_prompt(shot, scene),
                    "reference_images": char_refs + shot.reference_images,
                    "reference_videos": [shot.reference_video] if shot.reference_video else [],
                    "duration": shot.duration,
                    "camera_settings": {
                        "move": shot.camera_move,
                        "angle": shot.camera_angle
                    }
                })
        
        return config


def demo_2026():
    """2026版Pipeline演示 - 展示Seedance 2.0特性"""
    print("=" * 70)
    print("🎬 AI短剧 Pipeline 2026 Edition - Seedance 2.0")
    print("=" * 70)
    print("\n🆕 2026新特性:")
    print("  • 多模态输入: 9图+3视频+3音频+文本")
    print("  • 原生音频生成: 对白+环境音+音乐同步")
    print("  • 无需LoRA训练: 参考图直接锁定角色")
    print("  • 导演级运镜: 12种运镜+6种机位")
    print("  • 多镜头连贯: 一次生成保持角色一致")
    
    # 创建项目
    pm = PipelineManager2026()
    project = pm.create_project(
        name="2026赛博爱情故事",
        genre="scifi_romance",
        style="cinematic cyberpunk neon",
        video_backend="seedance-2.0",
        resolution="2k"  # 2026: 支持2K
    )
    print(f"\n✅ 创建项目: {project.name}")
    print(f"   后端: {project.video_backend}")
    print(f"   分辨率: {project.resolution}")
    
    # 添加角色 - 2026: 直接使用参考图，无需训练！
    pm.add_character(
        name="赛博女主",
        description="25岁黑客，蓝发，机械眼",
        reference_images=[
            "characters/reference_images/cyber_girl_01.jpg",
            "characters/reference_images/cyber_girl_02.jpg",
            "characters/reference_images/cyber_girl_03.jpg"
        ],
        reference_videos=["characters/reference_videos/cyber_girl_walk.mp4"],
        motion_style="dramatic"
    )
    
    pm.add_character(
        name="AI助手",
        description="全息投影AI，半透明，发光",
        reference_images=[
            "characters/reference_images/hologram_ai_01.jpg"
        ]
    )
    
    # 添加场景
    scene = pm.add_scene(
        title="初次相遇",
        description="女主在霓虹街头发现AI助手",
        location="cyberpunk city street, rainy night",
        time_of_day="night",
        mood="mysterious",
        ambient_track="rain and distant traffic"
    )
    
    # 添加镜头 - 2026: 完整运镜控制
    shot1 = pm.add_shot(
        scene_id=scene.scene_id,
        description="女主在雨中行走的全景",
        shot_type="wide",
        characters=["赛博女主"],
        camera_move="tracking",      # 跟踪镜头
        camera_angle="eye_level",
        duration=10,
        ambient_sound="heavy rain, neon buzz"
    )
    
    shot2 = pm.add_shot(
        scene_id=scene.scene_id,
        description="发现全息AI，惊讶表情",
        shot_type="closeup",
        characters=["赛博女主"],
        camera_move="zoom_in",       # 推镜头
        camera_angle="low_angle",    # 仰拍显力量
        emotion="surprised",
        dialogue="这是...什么？",
        duration=8,
        music_mood="mysterious"
    )
    
    shot3 = pm.add_shot(
        scene_id=scene.scene_id,
        description="AI助手缓缓现身，发光",
        shot_type="medium",
        characters=["AI助手"],
        camera_move="dolly_in",      # 移动镜头推进
        camera_angle="eye_level",
        emotion="mysterious",
        dialogue="你好，我在等你",
        duration=12,
        ambient_sound="electronic humming, digital particles"
    )
    
    print(f"\n✅ 添加 {len(scene.shots)} 个镜头")
    
    # 显示生成的Seedance优化提示词
    print("\n" + "=" * 70)
    print("📝 Seedance 2.0 优化提示词示例:")
    print("=" * 70)
    
    for shot in scene.shots:
        print(f"\n🎬 {shot.shot_id} ({shot.duration}秒)")
        print(f"   运镜: {shot.camera_move} + {shot.camera_angle}")
        print(f"   提示词预览:")
        print(f"   {shot.generation_prompt[:150]}...")
        if shot.dialogue:
            print(f"   💬 对白: '{shot.dialogue}' (Seedance原生生成语音)")
    
    # 导出配置
    config = pm.export_seedance_config()
    print(f"\n✅ 导出Seedance配置: {len(config['shots'])} 个镜头")
    
    print("\n" + "=" * 70)
    print("🚀 下一步: 设置API密钥并生成")
    print("=" * 70)
    print("\n代码:")
    print("  pm.set_api_key('your-seedance-api-key')")
    print("  pm.generate_scene('scene_001')")
    print("\n✨ 2026优势: 无需训练LoRA，无需后期配音，一次生成完整镜头！")
    print("=" * 70)
    
    return pm


if __name__ == "__main__":
    demo_2026()
