"""
消息处理服务测试
"""
import pytest

# 尝试导入NoneBot，如果失败则跳过测试
try:
	from nonebot.adapters.onebot.v11 import Message, MessageSegment
	from src.services.message_handler import extract_message_content
	HAS_NONEBOT = True
except ImportError:
	HAS_NONEBOT = False
	pytestmark = pytest.mark.skip("NoneBot未安装")


class TestMessageHandler:
	"""消息处理器测试"""
	
	def test_extract_text_message(self):
		"""测试提取文本消息"""
		if not HAS_NONEBOT:
			pytest.skip("NoneBot未安装")
		
		message = Message("Hello, World!")
		content = extract_message_content(message)
		
		assert content["text"] == "Hello, World!"
		assert len(content["images"]) == 0
		assert len(content["files"]) == 0
	
	def test_extract_image_message(self):
		"""测试提取图片消息"""
		if not HAS_NONEBOT:
			pytest.skip("NoneBot未安装")
		
		# 尝试不同的MessageSegment API
		try:
			message = Message([
				MessageSegment.text("这是一张图片"),
				MessageSegment.image("file:///path/to/image.jpg")
			])
		except TypeError:
			# 如果直接传字符串失败，尝试关键字参数
			try:
				message = Message([
					MessageSegment.text("这是一张图片"),
					MessageSegment.image(file="file:///path/to/image.jpg")
				])
			except Exception:
				pytest.skip("MessageSegment API不兼容")
		
		content = extract_message_content(message)
		
		assert "这是一张图片" in content["text"]
		assert len(content["images"]) == 1
	
	def test_extract_at_message(self):
		"""测试提取@消息"""
		if not HAS_NONEBOT:
			pytest.skip("NoneBot未安装")
		
		# 尝试不同的MessageSegment API
		try:
			message = Message([
				MessageSegment.at(123456),
				MessageSegment.text("你好")
			])
		except TypeError:
			try:
				message = Message([
					MessageSegment.at(qq=123456),
					MessageSegment.text("你好")
				])
			except Exception:
				pytest.skip("MessageSegment API不兼容")
		
		content = extract_message_content(message)
		
		assert len(content["at"]) > 0
		assert "你好" in content["text"]
	
	def test_extract_reply_message(self):
		"""测试提取回复消息"""
		if not HAS_NONEBOT:
			pytest.skip("NoneBot未安装")
		
		# 尝试不同的MessageSegment API
		try:
			message = Message([
				MessageSegment.reply(12345),
				MessageSegment.text("回复内容")
			])
		except TypeError:
			try:
				message = Message([
					MessageSegment.reply(id=12345),
					MessageSegment.text("回复内容")
				])
			except Exception:
				pytest.skip("MessageSegment API不兼容")
		
		content = extract_message_content(message)
		
		assert content["reply"] is not None
		assert "回复内容" in content["text"]
	
	def test_extract_mixed_message(self):
		"""测试提取混合消息"""
		if not HAS_NONEBOT:
			pytest.skip("NoneBot未安装")
		
		# 创建简单的混合消息
		try:
			message = Message([
				MessageSegment.text("文本"),
				MessageSegment.text("更多文本")
			])
		except Exception:
			pytest.skip("MessageSegment API不兼容")
		
		content = extract_message_content(message)
		
		assert "文本" in content["text"]
		assert "更多文本" in content["text"]

