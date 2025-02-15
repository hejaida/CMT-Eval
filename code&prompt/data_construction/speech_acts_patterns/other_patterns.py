#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import csv
import random
import json

evaluation_capabilities = ["上文记忆保持", "新旧知识整合", "用户反馈应对", "跨话题灵活性"]
speech_acts = ["追问", "建议", "补充", "修改", "反馈"]

eval_counter = [0, 0, 0, 0]

def load_queries_from_csv(filename):
    with open(filename, encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        queries = []
        for row in reader:
            queries.append({"id": row['ID'], "question": row['question'], "role": row['role']})  
        return queries

def get_next_evaluation_capability():
    global eval_counter
    min_count = min(eval_counter)
    index = eval_counter.index(min_count)
    eval_counter[index] += 1
    return evaluation_capabilities[index]

def generate_random_conversation(source_data):
    initial_query = source_data['question']
    source_data_id = source_data['id']  
    role = source_data['role'] 
    evaluation_ability = get_next_evaluation_capability()  
    num_rounds = random.randint(6, 8)
    

    conversation_content = [{"轮次": 1, "用户query": initial_query, "言语行为": "初始问题"}]
    used_speech_acts = []
    
    for round_num in range(2, num_rounds + 1):
        act = None
        if evaluation_ability == "上文记忆保持" or evaluation_ability == "跨话题灵活性":
            if round_num == 2 or round_num == num_rounds or round_num == num_rounds // 2:
                act = "追问"
        elif evaluation_ability == "新旧知识整合":
            if round_num == 2:
                act = "补充"
            elif round_num == num_rounds // 2:
                act = "修改"
            elif round_num == num_rounds - 2:
                act = "补充"
            elif round_num == num_rounds:
                act = "修改"
        elif evaluation_ability == "用户反馈应对":
            if round_num == 2:
                act = "反馈"
            elif round_num == num_rounds // 2:
                act = "建议"
            elif round_num == num_rounds - 2:
                act = "反馈"
            elif round_num == num_rounds:
                act = "建议"

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
        "origin_id": source_data_id,  D
        "评测能力": evaluation_ability,
        "用户角色": role,  
        "会话内容": conversation_content
    }
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

# 
