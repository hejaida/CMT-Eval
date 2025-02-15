#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pickle
import json
import random
from pypinyin import lazy_pinyin
import re

# 从pickle文件中读取常见错别字dict
def load_typos_dict(pickle_file_path):
    with open(pickle_file_path, 'rb') as f:
        typos_dict = pickle.load(f)
    print("常见错别字替换词典的一部分:", dict(list(typos_dict.items())[:5]))
    return typos_dict

def text_attack(json_file_path, typos_dict, default_typo_ratio, default_pinyin_ratio, output_file):
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for entry in data:
        conversations = entry.get('会话内容', [])
        role = entry.get('用户角色', '')

        # 根据用户角色调整
        typo_ratio = 1 / 4 if role == '齐业' else default_typo_ratio
        pinyin_ratio = 1 / 7 if role == '齐业' else default_pinyin_ratio

        num_queries = len(conversations)
        
        num_typos = max(1, int(num_queries * typo_ratio))
        
        typo_indices = random.sample(range(num_queries), num_typos)

        replaced_chars = {}

        for idx, conversation in enumerate(conversations):
            attacked_query = conversation['用户query']

            if idx in typo_indices:
                attacked_query = replace_typos(attacked_query, typos_dict, replaced_chars, num_replacements=1)

            attacked_query = replace_with_pinyin_before_punctuation(attacked_query, pinyin_ratio)

            conversation['用户query'] = attacked_query

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"攻击后的数据已保存至 {output_file}")

# 错别字
def replace_typos(text, typos_dict, replaced_chars, num_replacements=1):
    indices = [i for i, char in enumerate(text) if char in typos_dict and isinstance(typos_dict[char], dict)]
    if not indices:
        return text

    indices_to_replace = random.sample(indices, min(num_replacements, len(indices)))

    for index in indices_to_replace:
        char = text[index]
        if char in replaced_chars:
            typo = replaced_chars[char]
        else:
            typo_candidates = typos_dict[char].get('同音', [])
            if len(typo_candidates) > 3:
                typo_candidates = typo_candidates[:3]
            if typo_candidates:
                typo = random.choice(typo_candidates)
                replaced_chars[char] = typo
            else:
                continue

        text = text[:index] + typo + text[index+1:]

    return text

# 拼音替换
def replace_with_pinyin_before_punctuation(text, pinyin_ratio):
    result = []
    i = 0
    while i < len(text):
        char = text[i]
        if i < len(text) - 1 and re.match(r'[，。！？；：]', text[i + 1]):
            if '\u4e00' <= char <= '\u9fff' and random.random() < pinyin_ratio:
                char = lazy_pinyin(char)[0]
        result.append(char)
        i += 1
    return "".join(result)

pickle_file_path = ''
json_file_path = ''
output_file_path = ''

typos_dict = load_typos_dict(pickle_file_path)
text_attack(
    json_file_path=json_file_path,
    typos_dict=typos_dict,
    default_typo_ratio=1/6,        
    default_pinyin_ratio=1/7,      
    output_file=output_file_path
)
