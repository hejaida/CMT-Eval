#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
import json
import random
import aiohttp
import asyncio
import re
import os
import pandas as pd
import tracemalloc
import nest_asyncio
tracemalloc.start()
nest_asyncio.apply()

def load_prompt_from_txt(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as txtfile:
            prompt = txtfile.read().strip()
            print('Prompt读取成功')
            return prompt
    except FileNotFoundError:
        print(f"Error: 文件 {filename} 未找到")
        return None


async def assign_roles_to_questions(df, prompt, temperature, bnu_api_key, url):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for question in df['question']:
            tasks.append(fetch_role(session, question, prompt, temperature, bnu_api_key, url))

        roles = await asyncio.gather(*tasks)
        df['role'] = roles
        return df


async def fetch_role(session, question, prompt, temperature, bnu_api_key, url):

    input_prompt = f"{prompt}\n{question}"
    
    input_data = {
        "model": "",
        "messages": [
            {
                "role": "user",
                "content": input_prompt  
            }
        ],
        "temperature": temperature,
        "max_tokens": 10
    }

    if not bnu_api_key:
        raise ValueError("API key is missing")

    data = {
        'username': bnu_api_key,
        'request': json.dumps(input_data, ensure_ascii=False)
    }

    await asyncio.sleep(0.5)

    try:
        async with session.post(url, json=data) as response:
            response_text = await response.text()
            print(f"状态响应码: {response.status}")


            if response.status != 200:
                print(f"Error: 状态响应码: {response.status}")
                print(f"响应内容: {response_text}")
                return "Error"
            try:
                result = json.loads(response_text)

                if 'raw' in result:
                    raw_result = json.loads(result['raw'])
                    if 'choices' in raw_result and len(raw_result['choices']) > 0:
                        choice = raw_result['choices'][0]
                        if 'message' in choice and 'content' in choice['message']:
                            generated_content = choice['message']['content']
                            print("生成的内容:", generated_content)
                            return generated_content.strip()
                        elif 'text' in choice:
                            generated_content = choice['text']
                            print("生成的内容:", generated_content)
                            return generated_content.strip()
                        else:
                            print("Error: 无法找到生成的内容")
                            return "Error"
                    else:
                        print("Error: 'choices' 字段不存在或为空")
                        return "Error"
                else:
                    print("Error: 'raw' 字段不存在")
                    return "Error"

            except json.JSONDecodeError:
                print(f"Error: JSON 解析失败，响应内容: {response_text}")
                return "Error"

    except Exception as e:
        print(f"请求过程中发生异常: {e}")
        return "Error"


def save_to_csv(df, filename):

    if not os.path.exists(filename):
        df.to_csv(filename, mode='w', index=False)
    else:

        df.to_csv(filename, mode='a', index=False, header=False)
    print(f'已保存 {len(df)} 条处理后的数据。')

def read_and_process_in_chunks(input_csv, chunk_size, start_row):

    chunks = pd.read_csv(input_csv, chunksize=chunk_size, skiprows=range(1, start_row))
    return chunks



async def main():
    input_csv = ''  
    output_csv = ''  
    prompt_file = ''  
    temperature = 0.1

    url = ''
    api_key = ''

    prompt = load_prompt_from_txt(prompt_file)
    if prompt is None:
        return

    chunk_size = 
    start_row = 


    chunks = read_and_process_in_chunks(input_csv, chunk_size, start_row)

    for chunk in chunks:
        print(f"正在处理 {len(chunk)} 行数据...")

        df_with_roles = await assign_roles_to_questions(chunk, prompt, temperature, api_key, url)

        save_to_csv(df_with_roles, output_csv)

await main() 
