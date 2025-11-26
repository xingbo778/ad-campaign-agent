#!/usr/bin/env python3
"""Check if Gemini API is being called in creative service response."""
import sys
import json

data = json.load(sys.stdin)
llm_config = data['debug']['llm_config']

print('=== Gemini API 配置状态 ===')
print(f'API Key 已设置: {llm_config["gemini_api_key_set"]}')
print(f'API Key 长度: {llm_config["gemini_api_key_length"]}')
print(f'API Key 预览: {llm_config["gemini_api_key_preview"]}')
print(f'文本模型: {llm_config.get("gemini_model", "N/A")}')
print(f'文本模型已初始化: {llm_config["gemini_model_initialized"]}')
if "gemini_image_model" in llm_config:
    print(f'图片模型: {llm_config.get("gemini_image_model", "N/A")}')
    print(f'图片模型已初始化: {llm_config.get("gemini_image_model_initialized", False)}')

print(f'\n=== LLM 调用情况 ===')
raw_responses = data['debug'].get('raw_llm_responses', [])
print(f'总调用次数: {len(raw_responses)}')
for i, resp in enumerate(raw_responses[:6], 1):
    success = resp.get('success', False)
    resp_type = resp.get('type', 'unknown')
    status = '成功 (Gemini API)' if success else '失败/回退到模板'
    print(f'  {i}. {resp_type}: {status}')
    if success and 'response' in resp:
        print(f'     响应预览: {str(resp["response"])[:100]}...')

print(f'\n=== 生成的创意数量 ===')
print(f'创意数量: {len(data["creatives"])}')
if data['creatives']:
    print(f'第一个创意标题: {data["creatives"][0]["headline"]}')

