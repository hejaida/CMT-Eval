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


def load_samples_from_csv(filename, start, end=None, num_samples=None):
    try:
        data = pd.read_csv(filename)
        if end is not None:
            samples = data.iloc[start:end]
        elif num_samples is not None:
            samples = data.iloc[start:start + num_samples]
        else:
            samples = data.iloc[start:]
        samples = samples.to_dict(orient="records")
        print('读取CSV源数据成功。')
        return samples
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return []
    except pd.errors.EmptyDataError as e:
        print(f"Empty CSV file: {e}")
        return []

def load_prompt_from_txt(filename):
    with open(filename, 'r', encoding='utf-8') as txtfile:
        prompt = txtfile.read().strip()
        print('读取prompt成功')
        return prompt

def fetch_content(sample, prompt, temperature, bnu_api_key, url):
    prompt_with_text = f"{prompt}\n文本内容: {sample['text']}"
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt_with_text
                }
            ]
        }
    ]

    client = OpenAI(
        base_url=url,
        api_key=bnu_api_key
    )

    try:
        completion = client.chat.completions.create(
            model = 'anthropic/claude-3.5-sonnet',
            messages = messages
        )

        response_message = completion.choices[0].message.content
        print("生成的内容:", response_message)

        summary_match = re.search(r'"summary":\s*"(.*?)"', response_message, re.DOTALL)
        initial_question_match = re.search(r'"initial_question":\s*"(.*?)"', response_message, re.DOTALL)
        qa_pairs_match = re.search(r'"qa_pairs":\s*(\[[\s\S]*?\])', response_message, re.DOTALL)

        summary = summary_match.group(1) if summary_match else ""
        initial_question = initial_question_match.group(1) if initial_question_match else ""
        qa_pairs = qa_pairs_match.group(1) if qa_pairs_match else "[]"

        if summary or initial_question or qa_pairs: 
            output_data = {
                "ID": sample['ID'],
                "role": sample['role'],
                "text": sample['text'],
                "summary": summary,
                "initial_question": initial_question,
                "qa_pairs": qa_pairs  
            }

            print("输出数据:", output_data) 

            return output_data
        else:
            print("Error: 'content' key在raw响应中不存在或格式不正确")
            return None

    except Exception as e:
        print(f"Error during API call: {e}")
        return None

async def generate_content(samples, prompt, temperature, bnu_api_key, url):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_content(session, sample, prompt, temperature, bnu_api_key, url) for sample in samples]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]


def write_to_json_file(data, filename):
    try:
        with open(filename, 'r+', encoding='utf-8') as jsonfile:
            try:
                existing_data = json.load(jsonfile)
            except json.JSONDecodeError:
                existing_data = []
            existing_data.extend(data)
            jsonfile.seek(0)
            json.dump(existing_data, jsonfile, ensure_ascii=False, indent=2)
            print("写入数据到 JSON 文件成功。")
    except FileNotFoundError:
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2)
            print("新建 JSON 文件并写入数据成功。")

# In[ ]:


def main():
    raw_long-text_csv = ''  
    output_file = ''  
    prompt_filename = ''
    
    temperature = 0.1
    
    api_key = ''
    url = ''

    start = 
    num_samples = 

    try:
        samples = load_samples_from_csv(raw_long-text_csv, start=start, num_samples=num_samples)
        
        if not samples:
            print("No samples loaded.")
            return

        prompt = load_prompt_from_txt(prompt_filename)

        generated_contents = []
        for sample in samples:
            content = fetch_content(sample, prompt, temperature, api_key, url)
            if content:
                generated_contents.append(content)

        write_to_json_file(generated_contents, output_file)

        print(f"成功生成 {len(generated_contents)} 个会话并写入 {output_file}。")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

# 
