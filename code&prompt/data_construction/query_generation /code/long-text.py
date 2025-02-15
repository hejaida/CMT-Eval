#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
import json
import random
import pandas as pd 
import aiohttp
import asyncio
import re
import tracemalloc
import nest_asyncio
from openai import OpenAI
tracemalloc.start()
nest_asyncio.apply()


# In[ ]:


speech_acts = ["追问", "建议", "补充", "修改", "反馈"]

ROLE_FEATURES = {
    "陈旭": "男, 程序员, 爱质疑, 常用互联网黑话、术语，言简意赅",
    "朵朵": "女, 中学生, 好奇心强, 常用叠词、网络语",
    "张梅": "女, 教师, 善引导, 常用语气词",
    "齐业": "男, 企业职工, 爱反驳，表达直接, 常用方言俚语，常有语病",
    "Tina": "女, 编辑, 注重细节, 有时中英混用，用词丰富",
    "小刘": "男, 大学生, 表达夸张随性, 常用网络语、热梗",
    "雅婷": "女, 职场新人, 对模型回复要求高, 常反复确认信息",
    "王刚": "男, 银行职员, 考虑周全, 避免绝对化表达"
}

def load_data_from_json(filename, start_index, num_records):
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
        
        subset = data[start_index:start_index + num_records] if num_records else data[start_index:]
        
        queries = []
        for item in subset:
            queries.append({
                "ID": item['ID'],
                "role": item['role'],
                "initial_question": item['initial_question'],
                "summary": item['summary'],
                "qa_pairs": item['qa_pairs'],
                "text": item.get("text", "") 
        return queries


def generate_conversation_structure(source_data):
    initial_query = source_data['initial_question'] 
    role = source_data['role']
    evaluation_ability = "上文记忆保持"
    num_rounds = random.randint(6, 8)

    conversation_content = [{"轮次": 1, "用户query": initial_query, "言语行为": "初始问题"}]
    used_speech_acts = []

    for round_num in range(2, num_rounds + 1):
        act = None

        if round_num in [2, num_rounds, num_rounds // 2, num_rounds - 2]:
            act = "追问"
        if not act:
            available_acts = [a for a in speech_acts if a not in used_speech_acts]
            act = random.choice(available_acts) if available_acts else random.choice(speech_acts)

        used_speech_acts.append(act)

        conversation_content.append({
            "轮次": round_num,
            "用户query": "", 
            "言语行为": act
        })

    conversation_json = {
        "ID": source_data['ID'],
        "评测能力": evaluation_ability,
        "用户角色": role, 
        "summary": source_data['summary'],
        "qa_pairs": source_data['qa_pairs'],
        "text": source_data['text'],  
        "会话内容": conversation_content
    }
    return conversation_json

def load_prompt_from_txt(filename):
    with open(filename, 'r', encoding='utf-8') as txtfile:
        prompt = txtfile.read().strip()
        print('读取 prompt 成功')
        return prompt

async def generate_full_conversation(session, conversation_data, prompt_template, temperature, top_p, api_key, api_url):
    user_role = conversation_data.get("用户角色", "")
    role_features = ROLE_FEATURES.get(user_role, "")
    prompt_with_role = f"{prompt_template}\n### 角色特征: {role_features}"

    conversation_data_for_prompt = conversation_data.copy()
    conversation_data_for_prompt.pop('text', None)

    prompt_content = prompt_with_role + "\n" + json.dumps(conversation_data_for_prompt, ensure_ascii=False)

    client = OpenAI(base_url=api_url, api_key=api_key)

    try:
        completion = client.chat.completions.create(
            model='anthropic/claude-3.5-sonnet',
            messages=[
                {
                    "role": "user",
                    "content": prompt_content
                }
            ],
            temperature=temperature,
            top_p=top_p
        )

        response_message = completion.choices[0].message.content
        print("生成的会话内容:", response_message)

        generated_conversation = json.loads(response_message)
        return generated_conversation

    except Exception as e:
        print(f"Error during API call: {e}")
        return None
    
async def generate_conversations(conversation_samples, prompt_template, temperature, top_p, api_key, api_url):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for conversation in conversation_samples:
            conversation_data = generate_conversation_structure(conversation)

            task = generate_full_conversation(session, conversation_data, prompt_template, temperature, top_p, api_key, api_url)
            tasks.append(task)
        generated_conversations = await asyncio.gather(*tasks)


        final_conversations = []
        for gen_conv, original in zip(generated_conversations, conversation_samples):
            if gen_conv is not None:
                initial_query = f"{original.get('text', '')}\n{gen_conv['会话内容'][0].get('用户query', '')}"
                gen_conv["会话内容"][0]["用户query"] = initial_query
                final_conversations.append(gen_conv)
        return final_conversations

def save_transformed_data(transformed_data, output_file_path):
    try:
        with open(output_file_path, 'r+', encoding='utf-8') as output_file:
            try:
                existing_data = json.load(output_file)
            except json.JSONDecodeError:
                existing_data = []

            if isinstance(existing_data, list):
                if isinstance(transformed_data, list):
                    existing_data.extend(transformed_data)
                else:
                    existing_data.append(transformed_data)
            elif isinstance(existing_data, dict):
                if isinstance(transformed_data, dict):
                    existing_data.update(transformed_data)
                else:
                    print("现有数据是字典，新数据不是字典，无法合并！")
                    return
            output_file.seek(0)
            json.dump(existing_data, output_file, ensure_ascii=False, indent=2)
    except FileNotFoundError:

        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            json.dump(transformed_data, output_file, ensure_ascii=False, indent=2)

def main():
    input_json_filename = ''  # summary & QA 
    output_json_filename = ''  
    prompt_filename = ''

    temperature = 0.2
    top_p = 0.7

    api_key = ''
    api_url = ''

    start_index =
    num_records = 

    try:
        
        conversation_samples = load_data_from_json(input_json_filename, start_index=start_index, num_records=num_records)
        prompt_template = load_prompt_from_txt(prompt_filename)

        if not conversation_samples:
            print("未找到符合条件的会话样本。")
            return

        generated_conversations = asyncio.run(
            generate_conversations(conversation_samples, prompt_template, temperature, top_p, api_key, api_url)
        )
        if generated_conversations:
            save_transformed_data(generated_conversations, output_json_filename)
            print(f"成功生成 {len(generated_conversations)} 个会话并写入 {output_json_filename}。")
        else:
            print("未生成任何有效的会话内容。")

    except Exception as e:
        print(f"运行过程中发生错误: {e}")

if __name__ == "__main__":
    main()

# 
