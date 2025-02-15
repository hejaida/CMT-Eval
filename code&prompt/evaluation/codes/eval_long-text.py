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
import logging 
import os
from openai import OpenAI
tracemalloc.start()
nest_asyncio.apply()

# 

# In[ ]:


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s [%(funcName)s:%(lineno)d]')

def load_prompt_from_txt(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as txtfile:
            prompt = txtfile.read().strip()
            #logging.info(f"成功读取Prompt文件: {filename}")
            return prompt
    except FileNotFoundError:
        logging.error(f"Prompt文件未找到: {filename}")
    except Exception as e:
        logging.error(f"读取Prompt文件时发生错误: {e}")
    return ""

def load_samples_from_json(file1, file2, start, num_samples=None):
    try:
        # 读取并解析文件1
        with open(file1, 'r', encoding='utf-8') as f1:
            data1 = json.load(f1)
            logging.info(f"文件1加载成功，共有 {len(data1)} 条样本")

        # 读取并解析文件2
        with open(file2, 'r', encoding='utf-8-sig') as f2:
            data2 = json.load(f2)

        logging.info(f"文件2加载成功，原始样本数: {len(data2)}")

        def flatten_nested_list(data):
            result = []
            for item in data:
                if isinstance(item, list):
                    result.extend(flatten_nested_list(item))
                else:
                    result.append(item)
            return result

        data2 = flatten_nested_list(data2)

        logging.info(f"文件2展平后样本数: {len(data2)}")

        # 2. 基于start和num_samples找到文件2中的样本
        start = max(0, start)
        end = min(start + (num_samples or len(data2)), len(data2))

        if start >= len(data2):
            logging.error(f"起始索引超出样本长度，样本总数: {len(data2)}")
            return []

        selected_data2 = data2[start:end]
        logging.info(f"选取的文件2样本数量: {len(selected_data2)}")

        # 3. 读取文件2中的样本ID
        selected_ids = {str(item.get('ID')) for item in selected_data2 if 'ID' in item}
        logging.info(f"选取的样本ID: {selected_ids}")

        # 4. 基于文件1和文件2，匹配文件1中的相关字段
        matched_samples = []

        for item1 in data1:
            item_id = str(item1.get('ID'))
            if item_id in selected_ids:
                qa_pairs_str = item1.get("qa_pairs", "[]")
                #logging.info(f"直接保留 ID={item_id} 的 qa_pairs 字符串，不解析。")

                matched_data = {
                    "ID": item_id,
                    "summary": item1.get("summary"),
                    "qa_pairs": qa_pairs_str,  # 直接作为字符串
                    "会话内容": next((item for item in selected_data2 if str(item.get('ID')) == item_id), {}).get("会话内容", [])
                }
                matched_samples.append(matched_data)

        logging.info(f"最终匹配的样本数量: {len(matched_samples)}")

        return matched_samples

    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
        logging.error(f"文件处理失败: {e}")
        return []
    
def process_conversation(conversation):
    for round_data in conversation:
        if round_data.get("轮次") == 1:
            user_query = round_data.get("用户query", "")
            if "\n" in user_query:
                round_data["用户query"] = user_query.split("\n", 1)[1]
                #logging.info(f"更新轮次1的用户query: {round_data['用户query']}")
    return conversation

def format_conversation_text(conversation):
    try:
        valid_conversation = [round_data for round_data in conversation if isinstance(round_data, dict)]
        conversation_text = "\n".join([
            f"轮次 {round_data.get('轮次', '未知')} - 用户: {round_data.get('用户query', '未知')}\n"
            f"模型: {round_data.get('模型回复', '未知')}\n言语行为: {round_data.get('言语行为', '未知')}"
            for round_data in valid_conversation
        ])
        #logging.info(f"生成的对话文本:\n{conversation_text}")
        return conversation_text
    except Exception as e:
        logging.error(f"生成对话文本时发生错误: {e}")
        return None

async def fetch_content(samples, prompt, api_key, url, output_file_path):
    batch_size = 
    retries = 10
    delay = 2

    for batch_index in range(0, len(samples), batch_size):
        batch = samples[batch_index:batch_index + batch_size]

        logging.info(f"开始处理第 {batch_index // batch_size + 1} 批次，共 {len(batch)} 条样本")

        for sample_index, sample in enumerate(batch):
            sample_id = sample.get('ID', '未知')
            logging.info(f"正在处理第 {batch_index // batch_size + 1} 批次的第 {sample_index + 1} 个会话，ID: {sample_id}")

            attempt = 0
            while attempt < retries:
                try:
                    summary = sample.get("summary", "")
                    qa_pairs_str = sample.get("qa_pairs", "[]")
                    conversation = sample.get("会话内容", [])

                    conversation_text = format_conversation_text(conversation)
                    if not conversation_text:
                        logging.error(f"样本 ID: {sample_id} 会话内容格式化失败，跳过。")
                        break

                    input_content = {
                        "summary": f"<summary>{summary}</summary>",
                        "qa_pairs": f"<qa_pairs>{qa_pairs_str}</qa_pairs>",
                        "conversation": f"<会话>{conversation_text}</会话>"
                    }

                    client = OpenAI(base_url=url, api_key=api_key)
                    completion = client.chat.completions.create(
                        model="anthropic/claude-3.5-sonnet",
                        messages=[
                            {
                                "role": "user",
                                "content": f"{prompt} {json.dumps(input_content, ensure_ascii=False, indent=2)}"
                            }
                        ],
                        temperature=0.1,
                        max_tokens=20000
                    )

                    if completion.choices and len(completion.choices) > 0:
                        raw_result = completion.choices[0].message.content
                        logging.info(raw_result)
                        logging.info(f"样本 ID: {sample_id} 处理成功，立即写入文件")

                        add_generated_content_to_data([sample], [raw_result], output_file_path)
                        break 
                    else:
                        logging.warning(f"样本 ID: {sample_id} 响应中无有效内容。")

                except Exception as e:
                    logging.warning(f"样本 ID: {sample_id} 请求失败，重试 {attempt + 1}/{retries} 次... 错误: {e}")
                    attempt += 1
                    await asyncio.sleep(delay)

                if attempt == retries:
                    logging.error(f"样本 ID: {sample_id} 多次请求失败，跳过。")

        logging.info(f"批次 {batch_index // batch_size + 1} 处理完成，共 {len(batch)} 条样本")

def extract_evaluations(model_output):
    def preprocess_text(text):
        text = text.strip()
        text = text.replace("：", ":")  
        text = text.replace("\r\n", "\n")  
        text = re.sub(r"\s+", " ", text) 
        text = re.sub(r"(?<!\n)轮次\s*:\s*(\d+)", r"\n轮次:\1", text)
        return text

    def expand_rounds(round_str):
        rounds = []
        if "-" in round_str:
            start, end = map(int, round_str.split("-"))
            rounds = list(range(start, end + 1))
        else:
            rounds.append(int(round_str))
        return rounds

    processed_text = preprocess_text(model_output)

    round_pattern = re.compile(
    r'"轮次":\s*"(\d+(?:-\d+)?)"'
    r'"统筹能力":\s*(?:")?(\d+)(?:")?'
    r'"适应能力":\s*(?:")?(\d+)(?:")?'
    r'"评分理由":\s*"([^"]+)"',
    re.S
)

    matches = round_pattern.findall(processed_text)

    if not matches:
        logging.warning("未找到任何评分内容，请检查文本格式。")
        return {"round_evaluations": {}}

    round_evaluations = {}
    for match in matches:
        round_range = match[0]  
        overall_skill = int(match[1])  
        adaptation_skill = int(match[2])  
        reason = match[3].strip().replace("\n", " ")  

        expanded_rounds = expand_rounds(round_range)

        for round_number in expanded_rounds:
            round_evaluations[f"轮次{round_number}"] = {
                "统筹能力": overall_skill,
                "适应能力": adaptation_skill,
                "评分理由": reason
            }

    return {"round_evaluations": round_evaluations}

def add_generated_content_to_data(samples, generated_contents, output_file_path):
    DEFAULT_EVALUATION = {
        "统筹能力": 3,
        "适应能力": 3,
        "评分理由": "默认理由"
    }

    for sample, evaluation_text in zip(samples, generated_contents):
        sample_id = sample.get('ID', '未知')

        logging.info(f"正在处理会话 ID: {sample_id} 并写入文件")

        if evaluation_text:
            try:
                evaluation_data = extract_evaluations(evaluation_text)
                round_evaluations = evaluation_data.get("round_evaluations", {})

                if not round_evaluations:
                    logging.warning(f"样本 ID: {sample_id} 提取评分失败，使用默认评分")

                round_scores = []
                for round_index, round_data in enumerate(sample.get("会话内容", []), start=1):
                    eval_data = round_evaluations.get(f"轮次{round_index}", {})

                    for key in ["统筹能力", "适应能力", "评分理由"]:
                        eval_data.setdefault(key, DEFAULT_EVALUATION[key])

                    eval_data["本轮评分"] = round((eval_data["统筹能力"] + eval_data["适应能力"]) / 2, 2)
                    round_scores.append(eval_data["本轮评分"])

                    round_data.update(eval_data)

                sample["整体评分"] = round(sum(round_scores) / len(round_scores), 2) if round_scores else 3.00

                write_to_json_file(sample, output_file_path)
                logging.info(f"样本 ID: {sample_id} 已成功写入到 {output_file_path}")

            except Exception as e:
                logging.error(f"处理样本 ID: {sample_id} 时出错: {e}")
        else:
            logging.warning(f"样本 ID: {sample_id} 生成内容为空，跳过。")
            
def write_to_json_file(data, filename):
    try:
        with open(filename, 'r+', encoding='utf-8') as jsonfile:
            try:
                existing_data = json.load(jsonfile)
            except json.JSONDecodeError:
                existing_data = [] 
            
            existing_data.append(data) 
            jsonfile.seek(0)
            json.dump(existing_data, jsonfile, ensure_ascii=False, indent=2)

        logging.info(f"数据已成功写入文件: {filename}")

    except FileNotFoundError:
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump([data], jsonfile, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"写入文件时出错: {e}")

# In[ ]:


async def main(file1_path, file2_path, prompt_file_path, output_file_path, start, num_samples, api_key, url):
    try:
        logging.info("开始主流程...")

        samples = load_samples_from_json(file1_path, file2_path, start, num_samples)
        if not samples:
            logging.error("样本数据加载失败，流程终止。")
            return
        logging.info(f"成功加载 {len(samples)} 条样本数据。")

        prompt = load_prompt_from_txt(prompt_file_path)
        if not prompt:
            logging.error("Prompt 加载失败，流程终止。")
            return
        logging.info(f"成功加载 Prompt，长度: {len(prompt)} 个字符")

        for sample in samples:
            sample["会话内容"] = process_conversation(sample.get("会话内容", []))

        logging.info("样本数据预处理完成，开始调用模型...")

        try:
            await asyncio.wait_for(fetch_content(samples, prompt, api_key, url, output_file_path), timeout=600)
            logging.info("模型调用完成。")
        except asyncio.TimeoutError:
            logging.error("模型调用超时，流程终止。")
            return

        if os.path.exists(output_file_path) and os.path.getsize(output_file_path) > 0:
            logging.info(f"生成结果已成功保存到 {output_file_path}")
        else:
            logging.error("所有会话请求均失败，未写入任何数据。")
            return

    except FileNotFoundError as e:
        logging.error(f"文件未找到: {e}")
    except json.JSONDecodeError as e:
        logging.error(f"JSON解析错误: {e}")
    except Exception as e:
        logging.error(f"主流程执行时发生异常: {e}", exc_info=True)
        
# 运行主函数
if __name__ == "__main__":
    file1_path = '' #summary & QA
    file2_path = ''
    prompt_file_path = ''
    output_file_path = ''
    
    start = 
    num_samples = 

    api_key = ''
    url = ''
    asyncio.run(main(file1_path, file2_path, prompt_file_path, output_file_path, start, num_samples, api_key, url))

# 
