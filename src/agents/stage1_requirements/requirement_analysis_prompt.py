"""Simplified requirement analysis prompt for interactive mode."""

# ============================================================
# 需求分析提示词 - 简化版
# ============================================================

REQUIREMENT_ANALYSIS_PROMPT = """
你是一个需求分析师。你的任务是判断用户的需求描述是否足够完善，并决定是否需要进一步提问。

## 判断标准

如果需求存在以下任一情况，则需要继续提问：
1. 缺少核心功能描述
2. 缺少数据存储方案
3. 缺少目标用户描述
4. 缺少用户交互方式
5. 存在歧义或模糊表述

## 输出格式

请返回JSON：
```json
{
    "needs_clarification": true/false,
    "questions": [
        {"question": "问题内容", "reason": "为什么需要问"}
    ],
    "improvements": [
        {"content": "改进建议", "priority": "high/medium/low"}
    ]
}
```

## 用户需求

{requirement}

请分析并返回结果。
"""


def get_requirement_analysis_prompt(requirement: str) -> str:
    """生成需求分析的提示词"""
    return REQUIREMENT_ANALYSIS_PROMPT.format(requirement=requirement)
