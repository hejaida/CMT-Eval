#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
import json
import random
import aiohttp
import asyncio
import re
import tracemalloc
import nest_asyncio
tracemalloc.start()
nest_asyncio.apply()


# In[ ]:


def load_samples_from_json(filename, start, end=None, num_samples=None):
    try:
        with open(filename, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)

            if end is not None:
                samples = data[start:end]
            elif num_samples is not None:
                samples = data[start:start + num_samples]
            else:
                samples = data[start:]

            print('读取源数据成功。')
            return samples
    except json.JSONDecodeError as e:
        print(f"Error reading JSON file: {e}")
        return []
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return []

def load_prompt_from_txt(filename):
    with open(filename, 'r', encoding='utf-8') as txtfile:
        prompt = txtfile.read().strip()
        print('读取prompt成功')
        return prompt
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

async def fetch_content(session, sample, prompt, temperature, top_p, bnu_api_key, url):
    user_role = sample.get("用户角色", "")
    role_features = ROLE_FEATURES.get(user_role, "")
    prompt_with_role = f"{prompt}\n ###角色特征: {role_features} "

    input_data = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
            {
                "role": "user",
                "content": prompt_with_role + "\n" + json.dumps(sample, ensure_ascii=False) 
            }
        ],
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": 
    }

    if not bnu_api_key:
        raise ValueError("API key is missing")

    data = {
        'username': bnu_api_key,
        'request': json.dumps(input_data, ensure_ascii=False)
    }

    await asyncio.sleep(0.5)

    async with session.post(url, json=data) as response:
        response_text = await response.text()
        print(f"状态响应码: {response.status}")

        if response.status != 200:
            print(f"Error: 状态响应码: {response.status}")
            return None, 0, 0

        try:
            result = json.loads(response_text)
            print("Parsed JSON response:", json.dumps(result, ensure_ascii=False, indent=2))
        except json.JSONDecodeError:
            print(f"Error: 收到非json响应: {response_text}")
            return None, 0, 0

    if 'raw' in result:
        try:
            raw_result = json.loads(result['raw'])
            print("Parsed raw JSON:", json.dumps(raw_result, ensure_ascii=False, indent=2))  
            if 'content' in raw_result:
                generated_content = raw_result['content'][0]['text']  
                print("生成的内容:", generated_content)  
                print("模型调用成功")
            else:
                print("Error: 'content' key在raw响应中不存在")
                return None, 0, 0
        except json.JSONDecodeError:
            print(f"Error: 无法解析raw中的JSON: {result['raw']}")
            return None, 0, 0
    else:
        print("Error: 'raw' key在响应中不存在")
        return None, 0, 0

    credits_consumed = float(result.get('credits_consumed', '0').replace('$', ''))  
    credits_total = float(result.get('credits_total', '0').replace('$', '')) 
    print("额度计算完成。")

    return generated_content, credits_consumed, credits_total

async def generate_content(samples, prompt, temperature, top_p, bnu_api_key, url):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for sample in samples:
            tasks.append(fetch_content(session, sample, prompt, temperature, top_p, bnu_api_key, url))
        
        results = await asyncio.gather(*tasks)
        generated_contents = []
        total_credits_consumed = 0.0
        credits_list = []

        for result in results:
            if result and result[0] is not None:
                generated_content, credits_consumed, credits_total = result
                generated_contents.append(generated_content)

                total_credits_consumed += credits_consumed
                credits_list.append(credits_total)
        
        total_credits_total = min(credits_list) if credits_list else 0

        return generated_contents, total_credits_consumed, total_credits_total

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
    except FileNotFoundError:
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2)

# In[ ]:


def main():
    raw_json_file = ''  
    output_file = ''  
    prompt_filename = ''
    
    temperature = 0.3
    top_p = 0.7

    bnu_api_key = ''
    url = ''
    
    start = 
    num_samples = 

    try:
        samples = load_samples_from_json(raw_json_file, start=start, num_samples=num_samples)
        
        if not samples:
            print("No samples loaded.")
            return

        prompt = load_prompt_from_txt(prompt_filename)
        
        generated_contents, total_credits_consumed, total_credits_total = asyncio.run(
            generate_content(samples, prompt, temperature, top_p, bnu_api_key, url)
        )
    
        try:
            with open(output_file, 'r+', encoding='utf-8') as output_file:
                try:
                    existing_data = json.load(output_file)
                except json.JSONDecodeError:
                    existing_data = []  
                existing_data.extend(generated_contents)
                output_file.seek(0)
                json.dump(existing_data, output_file, ensure_ascii=False, indent=2)
        except FileNotFoundError:
            with open(output_file, 'w', encoding='utf-8') as output_file:
                json.dump(generated_contents, output_file, ensure_ascii=False, indent=2)

        print(f"成功生成 {len(generated_contents)} 个会话并写入 {output_file}。")
        print(f"已消耗额度: {total_credits_consumed}")
        print(f"总额度: {total_credits_total}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

print('数据生成完成。')

# In[ ]:


## 生成的数据格式转化
def clean_json_string(json_string):
    cleaned_string = re.sub(r'[\x00-\x1f\x7f]', '', json_string)
    return cleaned_string

def read_and_parse_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

        json_list = json.loads(content)

    parsed_data = []
    for item in json_list:
        try:
            cleaned_item = clean_json_string(item)  
            parsed_data.append(json.loads(cleaned_item))
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            print(f"有问题的字符串: {item}")

    return parsed_data

def transform_data(data):
    transformed_data = []
    
    for entry in data:
        transformed_entry = {
            "origin_id": entry.get("origin_id", ""),
            "评测能力": entry.get("评测能力", ""),
            "用户角色": entry.get("用户角色", ""),
            "会话内容": []
        }

        for dialog in entry.get("会话内容", []):
            transformed_entry["会话内容"].append({
                "轮次": dialog.get("轮次", ""),
                "用户query": dialog.get("用户query", ""),
                "言语行为": dialog.get("言语行为", ""),
                "预设回复": dialog.get("预设回复", ""),
                "难度设计方法": dialog.get("难度设计方法", "")
            })
        
        transformed_data.append(transformed_entry)
    
    return transformed_data

def save_transformed_data(transformed_data, output_file_path):
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(transformed_data, output_file, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    input_file_path = ''
    output_file_path = ''

    data = read_and_parse_json(input_file_path)

    transformed_data = transform_data(data)
    
    save_transformed_data(transformed_data, output_file_path)
    print("数据已成功转换并保存！")


# 
