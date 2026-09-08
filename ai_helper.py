"""
AI 试题解析客户端
支持 OpenAI 兼容接口格式，用户可在设置中配置 API 地址、密钥和模型
"""
import requests
import json
import re
from db import get_setting, set_setting


# 默认配置（DeepSeek）
DEFAULT_CONFIG = {
    "api_base": "https://api.deepseek.com",
    "api_key": "",
    "model": "deepseek-v4-flash",
    "timeout": 60,
}

# 预设AI服务配置
AI_PRESETS = {
    "deepseek": {
        "name": "DeepSeek",
        "api_base": "https://api.deepseek.com",
        "model": "deepseek-v4-flash",
        "desc": "官方最新模型，需充值",
    },
    "siliconflow": {
        "name": "硅基流动",
        "api_base": "https://api.siliconflow.cn/v1",
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "desc": "注册送¥14，小模型永久免费",
    },
    "doubao": {
        "name": "豆包（火山方舟）",
        "api_base": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "",
        "desc": "新用户送50万tokens，需填接入点ID",
    },
    "zhipu": {
        "name": "智谱GLM",
        "api_base": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash",
        "desc": "GLM-4-Flash永久免费，质量好",
    },
}


def get_preset_api_key(preset_name):
    """获取指定预设的API Key"""
    return get_setting(f"ai_key_{preset_name}", "")


def save_preset_api_key(preset_name, api_key):
    """保存指定预设的API Key"""
    set_setting(f"ai_key_{preset_name}", api_key)


def get_preset_model(preset_name):
    """获取指定预设的模型名"""
    return get_setting(f"ai_model_{preset_name}", AI_PRESETS[preset_name]["model"])


def save_preset_model(preset_name, model):
    """保存指定预设的模型名"""
    set_setting(f"ai_model_{preset_name}", model)


def get_ai_config():
    """获取 AI 配置（兼容旧版，返回当前默认配置）"""
    return {
        "api_base": get_setting("ai_api_base", DEFAULT_CONFIG["api_base"]),
        "api_key": get_setting("ai_api_key", DEFAULT_CONFIG["api_key"]),
        "model": get_setting("ai_model", DEFAULT_CONFIG["model"]),
        "timeout": int(get_setting("ai_timeout", DEFAULT_CONFIG["timeout"])),
    }


def save_ai_config(api_base, api_key, model, timeout=30):
    """保存 AI 配置（兼容旧版）"""
    set_setting("ai_api_base", api_base)
    set_setting("ai_api_key", api_key)
    set_setting("ai_model", model)
    set_setting("ai_timeout", str(timeout))


def clean_ai_output(text):
    """清理AI返回的内容，去除Markdown标记和重复内容"""
    if not text:
        return text

    # 去除Markdown标题标记
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    # 去除Markdown粗体/斜体标记
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    # 去除多余的空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 去除行首的特殊符号
    text = re.sub(r'^[►◆◇■□●○►◆★☆▶▷\s]+', '', text, flags=re.MULTILINE)

    # 检测并截断严重重复的内容（连续重复相同字符超过20次）
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # 检测行内是否有严重重复（如"选项D选项D选项D..."）
        if len(line) > 50:
            # 检查是否有连续重复的短片段
            has_repeat = False
            for length in [2, 3, 4, 5]:
                if len(line) > length * 3:
                    pattern = line[:length]
                    repeat_count = 0
                    pos = 0
                    while pos < len(line) - length:
                        if line[pos:pos+length] == pattern:
                            repeat_count += 1
                            pos += length
                        else:
                            break
                    if repeat_count > 5:
                        has_repeat = True
                        break
            if has_repeat:
                # 保留前50个字符，标记为内容异常
                line = line[:50] + "...（内容异常已截断）"
        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines).strip()


def analyze_question(question, options=None, q_type="single", preset_name=None):
    """
    调用 AI 解析题目
    question: 题干
    options: 选项列表
    q_type: 题型 single/multiple/judge/case
    preset_name: 预设名称 deepseek/siliconflow/doubao，为None时使用默认配置
    返回: 解析文本
    """
    if preset_name and preset_name in AI_PRESETS:
        preset = AI_PRESETS[preset_name]
        config = {
            "api_base": preset["api_base"],
            "api_key": get_preset_api_key(preset_name),
            "model": get_preset_model(preset_name),
            "timeout": int(get_setting("ai_timeout", DEFAULT_CONFIG["timeout"])),
        }
        if not config["api_key"]:
            return f"错误：{preset['name']} 未配置 API Key，请在设置中填写。"
        if not config["model"]:
            return f"错误：{preset['name']} 未配置模型名称，请在设置中填写。"
    else:
        config = get_ai_config()

    if not config["api_key"]:
        return "错误：未配置 API Key，请在设置中填写 AI 接口信息。"

    # 构建提示词
    type_names = {
        "single": "单选题",
        "multiple": "多选题",
        "judge": "判断题",
        "case": "案例分析题",
    }
    type_name = type_names.get(q_type, "题目")

    prompt = f"请解析以下{type_name}。\n\n"
    prompt += f"题目：{question}\n"

    if options and q_type in ("single", "multiple"):
        for i, opt in enumerate(options):
            letter = chr(65 + i)
            prompt += f"{letter}. {opt}\n"

    prompt += "\n要求：\n"
    prompt += "1. 直接给出解析，不要使用###、####等Markdown标记\n"
    prompt += "2. 语言简洁，条理清晰，分点说明\n"
    prompt += "3. 重点说明正确答案为什么对，错误选项为什么错\n"
    prompt += "4. 不要重复相同内容，不要输出无意义的重复文字\n"
    prompt += "5. 控制在300字以内"

    try:
        url = config["api_base"].rstrip("/") + "/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}",
        }
        data = {
            "model": config["model"],
            "messages": [
                {"role": "system", "content": "你是一个专业的考试辅导老师。回答要简洁、准确、条理清晰，禁止使用Markdown标记符号，禁止重复输出相同内容。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 600,
        }

        resp = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=config["timeout"]
        )
        resp.raise_for_status()
        result = resp.json()

        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"].strip()
            return clean_ai_output(content)
        else:
            return f"接口返回格式异常：{json.dumps(result, ensure_ascii=False)[:200]}"

    except requests.exceptions.Timeout:
        return "请求超时！可能原因：\n1. 网络较慢，请检查网络连接\n2. 模型响应慢，可在设置中将超时时间调大到60-120秒\n3. API地址或模型名有误，请检查配置\n\n建议：先点「测试连接」验证配置是否正确。"
    except requests.exceptions.ConnectionError:
        return "网络连接失败，请检查网络和 API 地址配置。"
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        try:
            err_data = e.response.json()
            err_msg = err_data.get("error", {}).get("message", "")
        except Exception:
            err_msg = e.response.text[:200]

        if status == 401:
            return "错误：API Key 无效，请检查 API Key 是否正确。"
        elif status == 402:
            return "错误：账户余额不足！请登录 DeepSeek 平台（https://platform.deepseek.com/）充值后再使用。"
        elif status == 404:
            return "错误：接口地址或模型名不存在，请检查 API 地址和模型名称。"
        elif status == 429:
            return "错误：请求过于频繁，请稍后再试。"
        else:
            return f"HTTP 错误 {status}：{err_msg}"
    except Exception as e:
        return f"解析失败：{str(e)}"


def generate_answer(question, options=None, q_type="single"):
    """
    调用 AI 生成答案（用于无答案的题目）
    返回: 答案文本
    """
    config = get_ai_config()

    if not config["api_key"]:
        return ""

    type_names = {
        "single": "单选题",
        "multiple": "多选题",
        "judge": "判断题",
        "case": "案例分析题",
    }
    type_name = type_names.get(q_type, "题目")

    prompt = f"请回答以下{type_name}，只给出答案，不要解释。\n\n"
    prompt += f"题目：{question}\n"

    if options and q_type in ("single", "multiple"):
        for i, opt in enumerate(options):
            letter = chr(65 + i)
            prompt += f"{letter}. {opt}\n"

    if q_type == "single":
        prompt += "\n请只回复选项字母（如 A）。"
    elif q_type == "multiple":
        prompt += "\n请只回复选项字母（如 ABC）。"
    elif q_type == "judge":
        prompt += "\n请只回复 正确 或 错误。"

    try:
        url = config["api_base"].rstrip("/") + "/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}",
        }
        data = {
            "model": config["model"],
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 50,
        }

        resp = requests.post(url, headers=headers, json=data, timeout=config["timeout"])
        resp.raise_for_status()
        result = resp.json()

        if "choices" in result and len(result["choices"]) > 0:
            answer = result["choices"][0]["message"]["content"].strip()
            # 清理答案
            if q_type == "single":
                m = re.search(r'[A-Z]', answer)
                return m.group(0) if m else answer
            elif q_type == "multiple":
                letters = sorted(set(re.findall(r'[A-Z]', answer)))
                return ''.join(letters) if letters else answer
            elif q_type == "judge":
                if any(k in answer for k in ['正确', '对', '√', 'T', 'True']):
                    return '正确'
                elif any(k in answer for k in ['错误', '错', '×', 'F', 'False']):
                    return '错误'
            return answer
        return ""

    except Exception:
        return ""
