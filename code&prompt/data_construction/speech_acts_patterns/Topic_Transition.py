#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import csv
import random
import json

speech_acts = ["追问", "建议", "补充", "修改", "反馈"]

def load_queries_from_csv(filename):
    with open(filename, encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        queries = []
        for row in reader:
            queries.append({"question": row['question'], "role": row['role']})
        return queries

def generate_random_conversation(source_data):
    initial_query = source_data['question']
    user_role = source_data['role']  
    num_rounds = random.randint(2, 3)
    
    conversation_content = [{"轮次": 1, "用户query": initial_query, "言语行为": "话题转移"}]
    used_speech_acts = []

    for round_num in range(2, num_rounds + 1):
        available_acts = [a for a in speech_acts if a not in used_speech_acts]
        act = random.choice(available_acts) if available_acts else random.choice(speech_acts)

        used_speech_acts.append(act) 
        conversation_content.append({"轮次": round_num, "用户query": "", "言语行为": act})

    conversation_json = {"用户角色": user_role, "会话内容": conversation_content}
    return conversation_json

try:
    queries = load_queries_from_csv('')
    if queries:
        all_conversations = []
        for source_data in queries:
            generated_conversation = generate_random_conversation(source_data)
            all_conversations.append(generated_conversation)
        
        print(json.dumps(all_conversations, ensure_ascii=False, indent=2))
    
        with open('', 'w', encoding='utf-8') as jsonfile:
            json.dump(all_conversations, jsonfile, ensure_ascii=False, indent=2)
    else:
        print("No queries loaded from CSV.")
except KeyError as e:
    print(f"KeyError: {e}")
except Exception as e:
    print(f"An error occurred: {e}")

# In[ ]:


import json
import random

def read_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")
        return None

def write_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def insert_b_into_a(a_data, b_data):
    a_cross_topic_data = [session for session in a_data if session.get("评测能力") == "跨话题灵活性"]

    if not a_cross_topic_data:
        print("没有找到评测能力为'跨话题灵活性'的会话")
        return a_data

    for index, session in enumerate(b_data):
        if "id" not in session:
            session["id"] = f"b_session_{index}"

    added_b_sessions = set()

    for a_session in a_cross_topic_data:
        a_user_role = a_session.get("用户角色", "").strip().lower()  
        matching_b_sessions = [
            session for session in b_data 
            if session.get("用户角色", "").strip().lower() == a_user_role and session.get("id") not in added_b_sessions
        ]
        
        if matching_b_sessions:
            b_session = random.choice(matching_b_sessions)  
            b_session_content = b_session.get("会话内容", [])

            
            added_b_sessions.add(b_session.get("id"))
        
            a_length = len(a_session.get("会话内容", []))
            if a_length < 3:
                print(f"A中的会话内容长度不足以插入B的会话，跳过该会话：{a_session}")
                continue

            insert_position = random.randint(2, max(2, a_length - 2))

            for i, b_round in enumerate(b_session_content):
                new_round = {
                    "轮次": insert_position + i + 1,
                    "用户query": b_round.get("用户query"),
                    "言语行为": b_round.get("言语行为"),
                    "预设回复": b_round.get("预设回复"),
                }
                a_session["会话内容"].insert(insert_position + i, new_round)


            for j, round_data in enumerate(a_session["会话内容"]):
                round_data["轮次"] = j + 1

            if (insert_position + len(b_session_content) < len(a_session["会话内容"]) 
                and isinstance(a_session["会话内容"][insert_position + len(b_session_content)], dict)):
                a_session["会话内容"][insert_position + len(b_session_content)]["言语行为"] = "话题转移"
            else:
                print(f"无法设置话题转移，插入位置超出或数据结构不匹配")

    return a_data


def main(a_file_path, b_file_path, output_file_path):
    a_data = read_json(a_file_path)
    b_data = read_json(b_file_path)
    
    if a_data is None or b_data is None:
        print("读取数据出错，无法继续执行")
        return
    
    modified_a_data = insert_b_into_a(a_data, b_data)
    write_json(modified_a_data, output_file_path)

    for session in modified_a_data[:3]: 
        print(json.dumps(session, ensure_ascii=False, indent=4))

a_file_path = '' # origintopic
b_file_path = '' # new topic
output_file_path = ''

main(a_file_path, b_file_path, output_file_path)

print('已将B中的数据及预设回复随机插入到A中的跨话题灵活性会话中')
