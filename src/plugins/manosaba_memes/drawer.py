# 桩模块：原 drawer 实现缺失，仅保证插件可被导入。
# 使用绘图功能时会抛出此错误，可后续补全实现或禁用本插件。

def draw_anan(text: str, face: str | None) -> bytes:
	raise NotImplementedError(
		"manosaba_memes: drawer 模块为占位实现，请补全 draw_anan 或禁用本插件。"
	)


def draw_trial(character, options) -> bytes:
	raise NotImplementedError(
		"manosaba_memes: drawer 模块为占位实现，请补全 draw_trial 或禁用本插件。"
	)
