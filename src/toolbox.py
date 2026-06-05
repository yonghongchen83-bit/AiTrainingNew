from __future__ import annotations

from typing import Iterable

from .models import Tool


class Toolbox:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._load_cold_start_tools()

    def _load_cold_start_tools(self) -> None:
        cold_start = [
            ("无法完成", "告知用户无法完成任务，解释错误代码并展示任务展开栈", True),
            ("无法锁定背景", "告知用户无法确定上下文并说明问题", True),
            ("调用外部工具", "按工具协议请求外部工具并给出理由", True),
            ("网络搜索", "按标准发起网络搜索，不可用时转为询问用户", True),
            ("请求澄清", "提示用户混淆点并请求澄清", True),
            ("请求资源扩展", "申请资源扩展并解释差距", True),
            ("合并工具", "搜索相似工具并尝试泛化合并", False),
            ("清理工具", "按协议删除不稳定或低价值工具", False),
            ("需要训练", "提交领域级训练请求并附样例", True),
            ("竖式加法", "用于多位数加法分步求解", False),
        ]
        for trigger, description, must_keep in cold_start:
            self._tools[trigger] = Tool(
                trigger=trigger,
                description=description,
                usage_count=0,
                cache_level="L1" if must_keep else "L2",
                must_keep=must_keep,
            )

    def query(self, context_text: str) -> list[Tool]:
        # 当前实现采用简单包含匹配，后续可替换为向量检索。
        ranked = list(self._tools.values())
        ranked.sort(key=lambda t: t.usage_count, reverse=True)
        return ranked

    def register(self, trigger: str, description: str) -> None:
        if trigger in self._tools:
            self._tools[trigger].usage_count += 1
            return
        self._tools[trigger] = Tool(
            trigger=trigger,
            description=description,
            usage_count=1,
            cache_level="L2",
            must_keep=False,
        )

    def use_tool(self, trigger: str | None) -> None:
        if not trigger:
            return
        tool = self._tools.get(trigger)
        if tool:
            tool.usage_count += 1

    def has_tool(self, trigger: str) -> bool:
        return trigger in self._tools

    def triggers(self) -> Iterable[str]:
        return self._tools.keys()
