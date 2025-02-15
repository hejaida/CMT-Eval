#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
import json
import random
import copy
import aiohttp
import asyncio
import re
import tracemalloc
import nest_asyncio
import dashscope
from openai import OpenAI
tracemalloc.start()
nest_asyncio.apply()
import os

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

def load_prompt_from_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            prompt = file.read().strip() 
            if not prompt:  
                print("Prompt file is empty. Proceeding with an empty prompt.")
                return ""  
            return prompt
    except FileNotFoundError:
        raise ValueError(f"Prompt file not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error loading prompt: {e}")

async def fetch_content_multi_round(session, conversation_history, api_key, temperature, max_tokens, url, retries=10):
    for attempt in range(retries):
        try:
            async with session.post(
                url=f"{url}/chat/completions",
                json={
                    "model": "",
                    "messages": conversation_history,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                headers={"Authorization": f"Bearer {api_key}"}
            ) as response:
                if response.status != 200:
                    raise ValueError(f"API Error: {response.status} - {await response.text()}")

                completion = await response.json()

                print(f"Raw completion response: {completion}")

                if "choices" in completion and len(completion["choices"]) > 0:
                    generated_content = completion["choices"][0]["message"]["content"]
                    print("Generated content:", generated_content)
                    return (
                        generated_content,
                        completion.get("usage", {}).get("completion_tokens", 0),
                        completion.get("usage", {}).get("total_tokens", 0),
                    )
                else:
                    print("Error: No valid content in response.")
                    return None, 0, 0

        except Exception as e:
            print(f"Attempt {attempt + 1}/{retries}: Error during request: {e}")
            if attempt < retries - 1:
                print("Retrying...")
            else:
                print("Exhausted retries.")
    return None, 0, 0

async def generate_content_multi_round(samples, prompt, api_key,temperature, max_tokens, url,output_file_path, batch_size=3, sleep_interval=2):
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(samples), batch_size):
            batch_samples = samples[i:i + batch_size]

            for sample in batch_samples:
                conversation_history = []

                original_data = {
                    "origin_id": sample.get("origin_id"),
                    "评测能力": sample.get("评测能力"),
                    "用户角色": sample.get("用户角色")
                }

                if prompt:
                    conversation_history.append({"role": "user", "content": prompt})

                for round_data in sample["会话内容"]:
                    query = round_data.get("用户query", "")
                    if query:
                        conversation_history.append({"role": "user", "content": query})

                        round_data_copy = copy.deepcopy(round_data)
                        round_data_copy.pop("预设回复", None)
                        round_data_copy.pop("难度设计方法", None)

                        generated_content, _, _ = await fetch_content_multi_round(
                            session,
                            copy.deepcopy(conversation_history),
                            api_key,
                            temperature,
                            max_tokens,
                            url=url
                        )

                        if generated_content:
                            conversation_history.append({"role": "assistant", "content": generated_content})
                            round_data["模型回复"] = generated_content

                print(f"Writing complete conversation for ID {sample['origin_id']} to file.")
                sample.update(original_data)

                try:
                    await write_to_json_file([sample], output_file_path)
                    print(f"Successfully written complete conversation for ID {sample['origin_id']} to {output_file_path}")
                except Exception as e:
                    print(f"Error writing complete conversation for ID {sample['origin_id']} to file: {e}")

            if i + batch_size < len(samples):
                print(f"Sleeping for {sleep_interval} seconds before processing next batch...")
                await asyncio.sleep(sleep_interval)
                
async def write_to_json_file(data, filename):
    try:
        with open(filename, 'r+', encoding='utf-8') as jsonfile:
            try:
                existing_data = json.load(jsonfile)
            except json.JSONDecodeError:
                existing_data = []  
            existing_data.append(data)  
            jsonfile.seek(0)
            json.dump(existing_data, jsonfile, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump([data], jsonfile, ensure_ascii=False, indent=2)


# In[ ]:


async def main(input_file_path, prompt_file_path, output_file_path, start, end=None, num_samples=None, api_key=None,temperature=0, max_tokens=8000,url=None):
    if not url or not isinstance(url, str):
        raise ValueError("Invalid URL. Please provide a valid URL string.")
    print(f"Initial URL type: {type(url)}, value: {url}")

    output_dir = os.path.dirname(output_file_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)  

    samples = load_samples_from_json(input_file_path, start=start, end=end, num_samples=num_samples)
    if not samples:
        raise ValueError("No samples loaded. Please check the input file and specified range.")
    print(f"Loaded {len(samples)} samples for processing.")

    prompt = load_prompt_from_txt(prompt_file_path)
    if not prompt:
        print("Notice: Prompt is empty. Proceeding without a system prompt.")

    try:
        await generate_content_multi_round(samples, prompt, api_key, temperature, max_tokens, url,output_file_path)
    except Exception as e:
        print(f"Error during content generation: {e}")
        return
    
if __name__ == "__main__":
    start = 
    num_samples = 
    temperature = 0.2
    max_tokens = 8000

    input_file_path = ''
    prompt_file_path = ''
    output_file_path = ''
    
    api_key = ''
    url = ''

try:
    asyncio.run(main(
        input_file_path=input_file_path,
        prompt_file_path=prompt_file_path,
        output_file_path=output_file_path,
        start=start,
        num_samples=num_samples,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        url=url
    ))
except Exception as e:
    print(f"Error running main function: {e}")
