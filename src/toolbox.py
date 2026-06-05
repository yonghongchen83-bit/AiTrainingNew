from __future__ import annotations

from typing import Iterable

from .models import Tool


class Toolbox:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._alias_to_name: dict[str, str] = {}
        self._load_cold_start_tools()

    def _load_cold_start_tools(self) -> None:
        # 冷启动工具箱：每个工具允许多个触发词（别名）。
        cold_start = [
            (
                "CompletionFailed",
                ["CompletionFailed", "Fail to complete", "无法完成"],
                "告知用户无法完成任务，解释错误代码并展示任务展开栈",
                True,
            ),
            (
                "FramingFailed",
                ["FramingFailed", "Fail to frame context", "无法锁定背景"],
                "告知用户无法确定上下文并说明问题",
                True,
            ),
            (
                "toolsApplication",
                ["toolsApplication", "Apply External Tool", "调用外部工具"],
                "使用标准工具调用协议请求外部工具并说明理由",
                True,
            ),
            (
                "webSearch",
                ["webSearch", "Search Web", "网络搜索"],
                "按标准发起网络搜索，不可用时转为询问用户",
                True,
            ),
            (
                "Ask User for clarification",
                ["Ask User for clarification", "请求澄清"],
                "提示用户混淆点并请求澄清",
                True,
            ),
            (
                "ToolsExtension",
                ["ToolsExtension", "Request resource extension", "请求资源扩展"],
                "申请资源扩展并解释差距",
                True,
            ),
            (
                "Merge Tool",
                ["Merge Tool", "合并工具"],
                "搜索相似工具并尝试泛化合并",
                False,
            ),
            (
                "Purge Tool",
                ["Purge Tool", "清理工具"],
                "按协议删除不稳定或低价值工具",
                False,
            ),
            (
                "TrainingRequired",
                ["TrainingRequired", "需要训练"],
                "提交领域级训练请求并附样例",
                True,
            ),
            (
                "vertical_addition",
                ["vertical_addition", "竖式加法"],
                "用于多位数加法分步求解",
                False,
            ),
        ]
        for name, trigger_words, description, must_keep in cold_start:
            self._tools[name] = Tool(
                name=name,
                trigger_words=trigger_words,
                description=description,
                usage_count=0,
                cache_level="L1" if must_keep else "L2",
                must_keep=must_keep,
            )
            for alias in trigger_words:
                self._alias_to_name[alias] = name

    def query(self, context_text: str) -> list[Tool]:
        # 当前实现采用简单包含匹配，后续可替换为向量检索。
        ranked = list(self._tools.values())
        ranked.sort(key=lambda t: t.usage_count, reverse=True)
        return ranked

    def register(self, trigger_words: list[str], description: str, name: str | None = None) -> None:
        canonical = name or trigger_words[0]
        if canonical in self._tools:
            self._tools[canonical].usage_count += 1
            for alias in trigger_words:
                self._alias_to_name[alias] = canonical
            return
        self._tools[canonical] = Tool(
            name=canonical,
            trigger_words=trigger_words,
            description=description,
            usage_count=1,
            cache_level="L2",
            must_keep=False,
        )
        for alias in trigger_words:
            self._alias_to_name[alias] = canonical

    def resolve(self, trigger_or_name: str) -> str | None:
        if trigger_or_name in self._tools:
            return trigger_or_name
        return self._alias_to_name.get(trigger_or_name)

    def use_tool(self, trigger_or_name: str | None) -> None:
        if not trigger_or_name:
            return
        canonical = self.resolve(trigger_or_name)
        if not canonical:
            return
        tool = self._tools.get(canonical)
        if tool:
            tool.usage_count += 1

    def has_tool(self, trigger_or_name: str) -> bool:
        return self.resolve(trigger_or_name) is not None

    def triggers(self) -> Iterable[str]:
        return self._alias_to_name.keys()
