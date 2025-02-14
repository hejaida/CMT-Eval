# CMT-Eval Dataset and Code

This project focuses on the dataset, code, and prompts used in CMT-Eval for multi-turn dialogue evaluation. Below is the directory structure:

## Code & Prompt

Contains the code and prompt files used for data construction and evaluation.

### Data Construction

Includes submodules related to dataset construction:

- **`long-text_summary&QA`**: Code and prompts for processing long texts into summaries and generating QA pairs.
- **`query_generation`**: Code and prompts for generating user queries across three subsets.
- **`speech_acts_patterns`**: Defines and constructs four speech act patterns to organize the dialogue structure.
- **`user_persona_match_data`**: Code and prompts used to match collected data with user personas.

### Evaluation

Contains code and prompts for evaluating multi-turn dialogues.

### Model Response

Contains the responses from different models for each dialogue turn.

### Post-processing

Code and list of character errors for for post-processing.

## Data

This folder contains data files for different subsets used in the project.

### Dialogue Data

Contains the user personas, user queries and corresponding speech acts. 

- Description of data format and key columns:
 - [origin_id]: Index in collected data
 - [评测能力]: Types of speech act patterns  
 - [用户query]: User queries
 - [用户角色]: User personas
 - [言语行为]: Speech acts per turn
 - [预设回复]: Claude's responses for query generation
 - [难度设计方法]: Conversational Challenge Strategies (Hard subset)
 - [模型回复]: Model responses
 - [统筹能力]: Information Synthesis score 
 - [适应能力]: Adaptability score
 - [本轮评分]: Turn-Level score
 - [整体评分]: Dialogue-level score

### Eval Data

Contains the results from the evaluation process.

### Model Response Data

Stores the model response data for each evaluation.


