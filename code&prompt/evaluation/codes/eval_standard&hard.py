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
from openai import OpenAI
import time
import os
import sys
tracemalloc.start()
nest_asyncio.apply()

# 

# In[ ]:


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s [%(funcName)s:%(lineno)d]')

def load_samples_from_json(filename, start_list, num_samples=None, batch_size=3, sleep_time_range=(1, 2), prompt=None, client=None, output_file_path=None):
    try:
        with open(filename, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)

            if not isinstance(data, list):
                logging.error(f"文件内容格式错误，应为列表: {filename}")
                return []

            flattened_data = [sample[0] for sample in data if isinstance(sample, list) and len(sample) > 0]

            for start in start_list:
                if start < 0 or (num_samples is not None and num_samples < 0):
                    logging.error(f"无效的参数: start={start}, num_samples={num_samples}")
                    continue

                if start >= len(flattened_data):
                    logging.error(f"起始行超出数据长度: 数据长度={len(flattened_data)}, start={start}")
                    continue

                end = start + num_samples if num_samples is not None else len(flattened_data)
                samples = flattened_data[start:end]
                logging.info(f"成功读取源数据: {len(samples)} 条记录 (范围: {start}-{end - 1 if num_samples else '末尾'}).")

                for i in range(0, len(samples), batch_size):
                    batch_samples = samples[i:i + batch_size]
                    logging.info(f"开始处理第 {i + 1}-{i + len(batch_samples)} 条样本")

                    for sample in batch_samples:
                        conversation = sample.get('会话内容', [])
                        if isinstance(conversation, list):
                            result = fetch_content(client, conversation, prompt)
                            if result:
                                add_generated_content_to_data([sample], [result], output_file_path)
                                logging.info(f"样本 {sample.get('origin_id', '未知')} 已成功写入")
                            else:
                                logging.warning(f"样本 {sample.get('origin_id', '未知')} 未能生成内容")
                        else:
                            logging.warning(f"样本 {sample.get('origin_id', '未知')} 的 '会话内容' 格式错误，跳过处理")

                    sleep_time = random.uniform(*sleep_time_range)
                    logging.info(f"批次处理完毕，暂停 {sleep_time:.2f} 秒")
                    time.sleep(sleep_time)

        return True
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"文件读取失败: {filename}, 错误: {e}")
    except Exception as e:
        logging.error(f"意外错误: {e}")
    return False

def load_prompt_from_txt(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as txtfile:
            prompt = txtfile.read().strip()
            logging.info(f"成功读取Prompt文件: {filename}")
            return prompt
    except FileNotFoundError:
        logging.error(f"Prompt文件未找到: {filename}")
    except Exception as e:
        logging.error(f"读取Prompt文件时发生错误: {e}")
    return ""

def fetch_content(client, conversation, prompt, max_retries=10, initial_wait=1):
    if not isinstance(conversation, list):
        logging.error(f"conversation 应该是一个字典列表，但收到类型: {type(conversation)}")
        return None

    valid_conversation = [round_data for round_data in conversation if isinstance(round_data, dict)]
    if not valid_conversation:
        logging.error("conversation 中没有有效的字典元素，无法生成对话文本。")
        return None

    try:
        conversation_text = "\n".join([
            f"轮次 {round_data.get('轮次', '未知')} - 用户: {round_data.get('用户query', '未知')}\n"
            f"模型: {round_data.get('模型回复', '未知')}\n言语行为: {round_data.get('言语行为', '未知')}"
            for round_data in valid_conversation
        ])
    except Exception as e:
        logging.error(f"生成对话文本时发生错误: {e}")
        return None

    input_content = {
        "conversation": conversation_text
    }

    for attempt in range(max_retries):
        try:
            logging.info(f"尝试调用模型: 第 {attempt + 1}/{max_retries} 次")

            completion = client.chat.completions.create(
                model="anthropic/claude-3.5-sonnet",
                messages=[
                    {
                        "role": "user",
                        "content": f"{prompt} <会话>{json.dumps(input_content, ensure_ascii=False, indent=2)}</会话>"
                    }
                ],
                temperature=0,
                top_p=0.1,
                max_tokens=20000,
                seed=12,
                stream=True
            )

            if completion.choices and len(completion.choices) > 0:
                generated_content = completion.choices[0].message.content
                logging.info(f"完整响应: {completion}")

                if generated_content:
                    logging.info(f"模型生成的内容:\n{generated_content}")
                    return generated_content
                else:
                    logging.error("模型生成的内容为空")
            else:
                logging.error("模型返回的 choices 字段为空或缺失")

        except Exception as e:
            logging.error(f"调用模型时发生错误: {e}")
            if attempt < max_retries - 1:
                wait_time = initial_wait * (2 ** attempt)  
                logging.info(f"将在 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                logging.error("已达到最大重试次数，无法完成请求。")
                return None

    return None


def extract_evaluations(model_output):
    def preprocess_text(text):
        """
        预处理文本，统一格式，确保数据一致性。
        """
        text = text.strip()
        text = text.replace("：", ":") 
        text = text.replace("\r\n", "\n") 
        text = re.sub(r"\s+", " ", text) 
        text = re.sub(r"(?<!\n)轮次\s*:\s*(\d+)", r"\n轮次:\1", text)
        return text

    def expand_rounds(round_str):
        """
        解析轮次信息，处理单个数字和范围（如6-8），返回轮次列表。
        """
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
    for i, sample in enumerate(samples):
        if i < len(generated_contents):
            evaluation_text = generated_contents[i]
            if evaluation_text:
                try:
                    evaluation_data = extract_evaluations(evaluation_text)
                    round_evaluations = evaluation_data.get("round_evaluations", {})

                    if not round_evaluations:
                        logging.warning(f"样本 {sample.get('origin_id', '未知')} 提取评分失败，将使用默认评分")

                    logging.info(f"提取的评分数据: {round_evaluations}")

                    round_scores = []  

                    for j, round_data in enumerate(sample.get("会话内容", []), start=1):
                        eval_data = round_evaluations.get(f"轮次{j}", {})  

                        for key in ["统筹能力", "适应能力", "评分理由"]:
                            if key not in eval_data:
                                logging.warning(f"轮次 {j} 的评分 {key} 缺失，使用默认值")
                                eval_data[key] = DEFAULT_EVALUATION[key]

                        eval_data["本轮评分"] = round((eval_data["统筹能力"] + eval_data["适应能力"]) / 2, 2)
                        round_scores.append(eval_data["本轮评分"])  

                        round_data.update(eval_data)

                    round_avg_score = round(sum(round_scores) / len(round_scores), 2) if round_scores else 3.00
                    sample["整体评分"] = round_avg_score

                    logging.info(f"样本 {sample.get('origin_id', '未知')} 更新完成，总轮次: {len(round_scores)}, 整体评分: {round_avg_score:.2f}")

                    write_to_json_file(sample, output_file_path)
                    logging.info(f"Successfully written complete conversation for origin_id {sample['origin_id']} to {output_file_path}")

                except Exception as e:
                    logging.error(f"处理样本 {sample.get('origin_id', '未知')} 时出错: {e}")
            else:
                logging.warning(f"样本 {sample.get('origin_id', '未知')} 生成内容为空，跳过。")
        else:
            logging.warning(f"未生成评估内容，样本 {sample.get('origin_id', '未知')} 跳过。")

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


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main(input_file_path, output_file_path, start_list, num_samples, api_key, url):
    try:
        logging.info(f"加载样本数据和 Prompt 内容...")

        if not os.path.exists(input_file_path):
            logging.error(f"输入文件不存在: {input_file_path}")
            sys.exit(1)

        prompt_file_path = os.path.abspath('')
        if not os.path.exists(prompt_file_path):
            logging.error(f"Prompt 文件不存在: {prompt_file_path}")
            sys.exit(1)

        prompt_content = load_prompt_from_txt(prompt_file_path)
        if not prompt_content:
            logging.error("Prompt 内容加载失败，流程终止。")
            sys.exit(1)

        logging.info("初始化...")
        client = OpenAI(base_url=url, api_key=api_key)

        success = load_samples_from_json(input_file_path, start_list, num_samples, prompt=prompt_content, client=client, output_file_path=output_file_path)

        if success:
            logging.info(f"所有样本已处理完毕，结果保存在 {output_file_path}")
        else:
            logging.error("样本处理过程中发生错误，未能完成处理。")

    except Exception as e:
        logging.error(f"主流程执行时发生异常: {e}", exc_info=True)
        
if __name__ == "__main__":
    input_file_path = ''
    prompt_file_path = ''
    output_file_path = ''
    start_list = []
    num_samples =

    api_key = ''
    url = ''
    
    prompt = load_prompt_from_txt(prompt_file_path)
    if not prompt:
        logging.error("Prompt 内容加载失败，流程终止。")
        exit(1)

    main(input_file_path, output_file_path, start_list, num_samples, api_key, url)

# 

# 

# 
