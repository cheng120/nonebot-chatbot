from typing import Set

from nonebot import get_driver
from pydantic import Field, BaseModel


class Config(BaseModel):
    disabled_plugins: Set[str] = Field(
        default_factory=set, alias="xiuxian_disabled_plugins"
    )
    priority: int = Field(2, alias="xiuxian_priority")


# 获取驱动配置并转换为字典
def _get_config_dict():
    """从驱动配置中提取配置字典"""
    driver_config = get_driver().config
    # 尝试多种方式转换为字典
    if hasattr(driver_config, 'model_dump'):
        # Pydantic v2
        return driver_config.model_dump()
    elif hasattr(driver_config, 'dict'):
        # Pydantic v1
        return driver_config.dict()
    elif isinstance(driver_config, dict):
        # 已经是字典
        return driver_config
    else:
        # 尝试获取属性
        config_dict = {}
        if hasattr(driver_config, 'xiuxian_disabled_plugins'):
            config_dict['xiuxian_disabled_plugins'] = getattr(driver_config, 'xiuxian_disabled_plugins', set())
        if hasattr(driver_config, 'xiuxian_priority'):
            config_dict['xiuxian_priority'] = getattr(driver_config, 'xiuxian_priority', 2)
        return config_dict


config = Config.model_validate(_get_config_dict())
priority = config.priority