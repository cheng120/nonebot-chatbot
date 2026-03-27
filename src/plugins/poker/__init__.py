import asyncio
from nonebot import on_command, on_notice, get_driver
from nonebot.permission import SUPERUSER
from nonebot.rule import Rule
from nonebot.message import run_preprocessor
from nonebot.plugin import PluginMetadata
from nonebot.params import Depends, CommandArg
from nonebot.internal.matcher import Matcher
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, NoticeEvent, MessageSegment, Message
from nonebot.adapters.onebot.v11.permission import GROUP, GROUP_ADMIN, GROUP_OWNER
from .utils import *


__plugin_meta__ = PluginMetadata(
	name="扑克对决",
	description="参考小游戏合集重写的扑克对决，大部分操作支持“按钮”，规则请看https://github.com/MoonofBridge24/nonebot_plugin_poker",
	usage="扑克对决/卡牌对决/接受：发起或接受对决\n重置对决：允许参与者或者群管重置本群对决\n出牌 1/2/3：出牌命令，当按钮失效的时候可以使用命令\n规则请看https://github.com/MoonofBridge24/nonebot_plugin_poker",
	type="application",
	homepage="https://github.com/MoonofBridge24/nonebot_plugin_poker",
	supported_adapters={"nonebot.adapters.onebot.v11"},
)


HELP_TEXT = (
	"【扑克对决 使用说明】\n"
	"发起对决：\n"
	"  - 扑克对决 / 卡牌对决\n"
	"  - 自己再次发送可以与 BOT 对战\n"
	"接受对决：\n"
	"  - 发送“接受”\n"
	"  - 或点击机器人提示消息上的表情按钮\n"
	"出牌：\n"
	"  - 轮到你时发送“出牌 1/2/3”\n"
	"重置对决：\n"
	"  - 群管或正在对战的玩家发送“重置对决”\n"
	"结算规则：\n"
	"  - 双方初始：HP=20，先手 DEF=0，后手 DEF=5，SP=10\n"
	"  - 任意一方 HP < 0 判负，牌堆用完则 HP 高者胜\n"
	"  - 详细数值与牌面效果请发送“扑克规则”查看"
)

RULES_TEXT = (
	"【扑克对决 规则说明】\n"
	"基础：\n"
	"  - 初始 HP=20，先手 DEF=0，后手 DEF=5，双方 SP=10\n"
	"  - 每轮进攻方抽 3 张牌，从中选 1 张打出\n"
	"  - 防守方若 SP>0，可能自动打出防守技能牌\n"
	"  - 结算后 DEF>10 变为 10；0<DEF≤10 自动-2；DEF 可为负并影响伤害\n"
	"结束条件：\n"
	"  - 任意一方 HP<0：另一方获胜\n"
	"  - 牌堆用完仍未分胜负：HP 高者获胜\n"
	"  - HP≥45 且防守结算后仍>45：视为肉身成圣\n"
	"牌面效果（点数记为 p）：\n"
	"  - 普通牌：♠ 防御 DEF+p，♥ 回血 HP+p，♣ 技能 SP+p，♦ 攻击 ATK=p\n"
	"  - 进攻技能：\n"
	"    ♠ 盾击：对方 HP-p/2，自身 DEF+p/2\n"
	"    ♥ 吸血：自身 HP+p/2，下次攻击按伤害再吸一半\n"
	"    ♣ 吟唱：SP+p 并额外打一张随机技能牌\n"
	"    ♦ 燃血：自身 HP-p/2，对方 HP-1.5p\n"
	"  - 防守技能：\n"
	"    ♠ 碎甲：自身 DEF+p/2，本回合受伤则令对方 DEF-p\n"
	"    ♥ 再生：自身 HP+p/2，本回合受伤则再+ p\n"
	"    ♣ 震慑：不耗 SP，使对方 SP-p\n"
	"    ♦ 反击：对方 HP-p/2，本回合受伤则反伤 50%（无视防御）\n"
	"ACE 特性：\n"
	"  - 打出 A 时掷 1D6 替换点数，并将本回合三张牌都作为技能牌结算"
)


poker = on_command("卡牌对决", aliases={"接受", "扑克对决"}, permission=GROUP)
hand_out = on_command("出牌", permission=GROUP)
reset_game = on_command("重置对决", permission=GROUP)
poker_help = on_command("扑克帮助", aliases={"扑克对决帮助"}, permission=GROUP)
poker_rules = on_command("扑克规则", aliases={"扑克对决规则"}, permission=GROUP)
reaction_poker = on_notice(rule_of_reaction(rule="regex", args=[r"\(1分钟后自动超时\)$", r"再来一局$"], codes=["424"]), priority=5, block=True)
reaction_hand_out = on_notice(rule_of_reaction(rule="keyword", args=["出牌 1/2/3"], codes=["123", "79", "124"]), priority=5, block=True)


poker_state = {}
async def reset(group: int = 0):
    '数据初始化'
    global poker_state
    if not group: poker_state = {}
    else: poker_state[group] = {
        'time': int(time.time()),
        'player1': {
            'uin': 0,
            'name': '',
            'HP': 20.0,
            'ATK': 0,
            'DEF': 0.0,
            'SP': 10,
            'suck': 0,
            'hand': []
        },
        'player2': {
            'uin': 0,
            'name': '',
            'HP': 20.0,
            'ATK': 0,
            'DEF': 5.0,
            'SP': 10,
            'suck': 0,
            'hand': []
        },
        'deck': [],
        'winer': ''
    }


driver = get_driver()
@driver.on_startup
async def on_startup_():
    await reset()


@run_preprocessor
async def _(event: GroupMessageEvent):
    now_time = event.time
    keys = [key for key in poker_state.keys() if (now_time - poker_state[key]['time'] > 90)]
    for key in keys:
        del poker_state[key]


@reaction_poker.handle()
@poker.handle()
async def _(bot: Bot, event: GroupMessageEvent | NoticeEvent, matcher : Matcher):
    '发起对决'
    group_id = event.group_id # type: ignore
    reaction = isinstance(event, NoticeEvent)
    if not group_id in poker_state: await reset(group_id)
    state = poker_state[group_id]
    if state['player1']['hand']: await matcher.finish('有人正在对决呢，等会再来吧~') if not reaction else await matcher.finish()
    if reaction:
        user_id = event.dict()['user_id']
        user_info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
        nickname = user_info['card'] or user_info['nickname']
    else:
        user_id = event.user_id
        nickname = event.sender.card or event.sender.nickname or ''
    state['time'] = event.time
    await start_game(bot, matcher, group_id, user_id, nickname, state)


@reaction_hand_out.handle()
@hand_out.handle()
async def _(bot: Bot, event: GroupMessageEvent | NoticeEvent, matcher : Matcher, args: Message | None = CommandArg()):
    '出牌判定'
    group_id = event.group_id # type: ignore
    reaction = isinstance(event, NoticeEvent)
    if reaction:
        user_id = event.dict()['user_id']
        match event.dict()['likes'][0]['emoji_id']:
            case '123':
                choice = 1
            case '79':
                choice = 2
            case '124':
                choice = 3
    else:
        user_id = event.user_id
        choice = int(args.extract_plain_text().strip()) # type: ignore
    if not group_id in poker_state: await reset(group_id)
    state = poker_state[group_id]
    if not state['player1']['hand']:
        await matcher.finish('对决还没开始呢，发起一轮新对决吧~') if not reaction else await matcher.finish()
    if state['player1']['uin'] != user_id:
        await matcher.finish('没牌的瞎出干什么') if not reaction else await matcher.finish()
    if not choice or not (choice in range(1, len(state['player1']['hand'])+1)):
        await matcher.finish('请正确输入出牌序号') if not reaction else await matcher.finish()
    state['time'] = event.time
    await process_hand_out(bot, matcher, group_id, choice, state)


async def start_game(bot: Bot, matcher : Matcher, group_id: int, user_id: int, nickname: str, state: PokerState):
    if not state['player1']['uin']:
        state['player1']['uin'] = user_id
        state['player1']['name'] = nickname
        msg_id = await matcher.send(f'{nickname} 发起了一场对决，正在等待群友接受对决...\n(1分钟后自动超时)')
        await asyncio.sleep(0.5)
        try:
            await bot.set_msg_emoji_like(message_id = msg_id['message_id'], emoji_id = '424', set = True)
        except Exception as e:
            print(e)
        return
    state['player2']['name'] = nickname
    if state['player1']['uin'] == user_id: state['player2']['name'] = 'BOT'
    else: state['player2']['uin'] = user_id
    if random.randint(0, 1): state['player1']['name'], state['player2']['name'], state['player1']['uin'], state['player2']['uin'] = state['player2']['name'], state['player1']['name'], state['player2']['uin'], state['player1']['uin']
    await matcher.send('唰唰唰 正在洗牌...')
    await asyncio.sleep(0.5)
    msg = await info_show(state)
    if not state['player1']['uin']:
        pick = random.randint(1, len(state['player1']['hand']))
        await matcher.send(msg)
        await process_hand_out(bot, matcher, group_id, pick, state)
        await matcher.finish()
    msg_id = await matcher.send(MessageSegment.at(state['player1']['uin']) + msg)
    await asyncio.sleep(0.5)
    for i in ['123', '79', '124']:
        await asyncio.sleep(0.5)
        try:
            await bot.set_msg_emoji_like(message_id = msg_id['message_id'], emoji_id = i, set = True)
        except Exception as e:
            print(e)


async def process_hand_out(bot: Bot, matcher : Matcher, group_id: int, choice: int, state: PokerState):
    msgs = await play_poker(state, choice - 1)
    msg = await info_show(state)
    while not state['player1']['uin'] and not state['winer']:
        msgs.append(msg)
        pick = random.randint(1, len(state['player1']['hand']))
        msgs += await play_poker(state, pick - 1)
        msg = await info_show(state)
    for i in msgs: await matcher.send(i)
    if state['winer']:
        await reset(group_id)
        msg_id = await matcher.send(msg)
        await asyncio.sleep(0.5)
        try:
            await bot.set_msg_emoji_like(message_id = msg_id['message_id'], emoji_id = '424', set = True)
        except Exception as e:
            print(e)
    else:
        msg_id = await matcher.send(MessageSegment.at(state['player1']['uin']) + msg)
        await asyncio.sleep(0.5)
        try:
            for i in ['123', '79', '124']:
                await asyncio.sleep(0.5)
                await bot.set_msg_emoji_like(message_id = msg_id['message_id'], emoji_id = i, set = True)
        except Exception as e:
            print(e)


@reset_game.handle()
async def _(bot: Bot, event: GroupMessageEvent, matcher : Matcher):
    group_id = event.group_id
    if not group_id in poker_state: await reset(group_id)
    state = poker_state[group_id]
    if event.sender.role != 'admin' and not event.user_id in [state['player1']['uin'], state['player2']['uin']]:
        await matcher.finish('你无权操作，请稍后再试')
    await reset(group_id)
    msg_id = await matcher.send('重置成功，点击按钮再来一局')
    await asyncio.sleep(0.5)
    try:
        await bot.set_msg_emoji_like(message_id = msg_id['message_id'], emoji_id = '424', set = True)
    except Exception as e:
        print(e)


@poker_help.handle()
async def _(matcher: Matcher):
	await matcher.finish(HELP_TEXT)


@poker_rules.handle()
async def _(matcher: Matcher):
	await matcher.finish(RULES_TEXT)

