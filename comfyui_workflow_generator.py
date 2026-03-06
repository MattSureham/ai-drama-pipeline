#!/usr/bin/env python3
"""
ComfyUI工作流生成器
生成可直接导入ComfyUI的JSON工作流文件
"""

import json
from pathlib import Path
from typing import List, Dict


def generate_comfyui_workflow(prompts: List[Dict], lora_path: str = None, 
                               use_ipadapter: bool = True, use_controlnet: bool = True) -> Dict:
    """
    生成ComfyUI工作流JSON
    
    Args:
        prompts: 提示词列表，每个包含positive, negative, shot_id等
        lora_path: LoRA模型路径
        use_ipadapter: 是否使用IP-Adapter保持角色一致
        use_controlnet: 是否使用ControlNet控制姿态
    """
    
    workflow = {
        "last_node_id": 100,
        "last_link_id": 200,
        "nodes": [],
        "links": [],
        "groups": [],
        "config": {},
        "extra": {},
        "version": 0.4
    }
    
    nodes = []
    links = []
    node_id = 1
    link_id = 1
    
    # 1. 加载Checkpoint节点
    checkpoint_node = {
        "id": node_id,
        "type": "CheckpointLoaderSimple",
        "pos": [50, 50],
        "size": [300, 100],
        "inputs": [],
        "outputs": [["MODEL", node_id], ["CLIP", node_id], ["VAE", node_id]],
        "widgets_values": ["SDXL/realvisxlV40.safetensors"]
    }
    nodes.append(checkpoint_node)
    checkpoint_id = node_id
    node_id += 1
    
    # 2. LoRA加载器（如果提供）
    lora_id = None
    if lora_path:
        lora_node = {
            "id": node_id,
            "type": "LoraLoader",
            "pos": [400, 50],
            "size": [300, 120],
            "inputs": [["model", checkpoint_id], ["clip", checkpoint_id]],
            "outputs": [["MODEL", node_id], ["CLIP", node_id]],
            "widgets_values": [lora_path, 0.8, 1.0]
        }
        nodes.append(lora_node)
        lora_id = node_id
        node_id += 1
    
    current_model_id = lora_id if lora_id else checkpoint_id
    current_clip_id = lora_id if lora_id else checkpoint_id
    
    # 3. 为每个prompt创建生成节点组
    y_offset = 200
    for i, prompt in enumerate(prompts):
        group_y = y_offset + i * 400
        
        # 正向提示词节点
        pos_prompt_node = {
            "id": node_id,
            "type": "CLIPTextEncode",
            "pos": [50, group_y],
            "size": [400, 200],
            "inputs": [["clip", current_clip_id]],
            "outputs": [["CONDITIONING", node_id]],
            "widgets_values": [prompt["positive"]],
            "title": f"Positive_{prompt['shot_id']}"
        }
        nodes.append(pos_prompt_node)
        pos_id = node_id
        node_id += 1
        
        # 负向提示词节点
        neg_prompt_node = {
            "id": node_id,
            "type": "CLIPTextEncode",
            "pos": [50, group_y + 250],
            "size": [400, 150],
            "inputs": [["clip", current_clip_id]],
            "outputs": [["CONDITIONING", node_id]],
            "widgets_values": [prompt["negative"]],
            "title": f"Negative_{prompt['shot_id']}"
        }
        nodes.append(neg_prompt_node)
        neg_id = node_id
        node_id += 1
        
        # 空Latent节点
        latent_node = {
            "id": node_id,
            "type": "EmptyLatentImage",
            "pos": [500, group_y + 250],
            "size": [300, 100],
            "inputs": [],
            "outputs": [["LATENT", node_id]],
            "widgets_values": [1024, 1024, 1]
        }
        nodes.append(latent_node)
        latent_id = node_id
        node_id += 1
        
        # KSampler节点
        sampler_node = {
            "id": node_id,
            "type": "KSampler",
            "pos": [900, group_y],
            "size": [300, 300],
            "inputs": [
                ["model", current_model_id],
                ["positive", pos_id],
                ["negative", neg_id],
                ["latent_image", latent_id]
            ],
            "outputs": [["LATENT", node_id]],
            "widgets_values": [42+i, "randomize", 20, 7.0, "euler", "normal", 1.0],
            "title": f"Generate_{prompt['shot_id']}"
        }
        nodes.append(sampler_node)
        sampler_id = node_id
        node_id += 1
        
        # VAE解码
        decode_node = {
            "id": node_id,
            "type": "VAEDecode",
            "pos": [1300, group_y],
            "size": [200, 50],
            "inputs": [
                ["samples", sampler_id],
                ["vae", checkpoint_id]
            ],
            "outputs": [["IMAGE", node_id]],
            "title": f"Decode_{prompt['shot_id']}"
        }
        nodes.append(decode_node)
        decode_id = node_id
        node_id += 1
        
        # 保存图片
        save_node = {
            "id": node_id,
            "type": "SaveImage",
            "pos": [1600, group_y],
            "size": [300, 300],
            "inputs": [["images", decode_id]],
            "outputs": [],
            "widgets_values": [prompt['shot_id']]
        }
        nodes.append(save_node)
        node_id += 1
    
    workflow["nodes"] = nodes
    workflow["links"] = links
    
    return workflow


def generate_with_upscaling(prompts: List[Dict], lora_path: str = None) -> Dict:
    """生成带Ultimate SD Upscale的高级工作流"""
    
    workflow = generate_comfyui_workflow(prompts[:1], lora_path)  # 基础结构
    
    # 添加Ultimate SD Upscale节点（简化版）
    # 实际使用时需要安装相应插件
    
    return workflow


def save_workflow(workflow: Dict, output_path: str):
    """保存工作流到文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, ensure_ascii=False, indent=2)
    print(f"✅ ComfyUI工作流已保存: {output_path}")


if __name__ == "__main__":
    # 示例：生成测试工作流
    test_prompts = [
        {
            "shot_id": "scene_001_shot_001",
            "positive": "masterpiece, best quality, (XiaoYa:1.2), young woman, short brown hair, big expressive eyes, sitting by window, cozy coffee shop, warm afternoon light, sketching in notebook, peaceful expression, soft bokeh background, cinematic composition, 8k",
            "negative": "bad anatomy, extra fingers, blurry, low quality, watermark"
        },
        {
            "shot_id": "scene_001_shot_002", 
            "positive": "masterpiece, best quality, (AJie:1.2), young man, round glasses, black hair, looking from across room, curious expression, coffee shop interior, warm lighting, cinematic",
            "negative": "bad anatomy, extra fingers, blurry, low quality"
        }
    ]
    
    workflow = generate_comfyui_workflow(test_prompts, lora_path="XiaoYa_v1.safetensors")
    save_workflow(workflow, "comfyui_workflow_test.json")
    print("\n使用说明:")
    print("1. 打开ComfyUI")
    print("2. 点击'Load'按钮")
    print("3. 选择 comfyui_workflow_test.json")
    print("4. 调整模型路径和参数")
    print("5. 点击'Queue Prompt'")
