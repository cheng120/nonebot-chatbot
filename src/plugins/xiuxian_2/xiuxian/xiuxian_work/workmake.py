from .reward_data_source import *
import random
from ..item_json import Items
from ..xiuxian_config import USERRANK
from ..xiuxian2_handle import OtherSet


def workmake(work_level, exp, user_level, accept_count=0, is_superuser=False):
    if work_level == '江湖好手':
        work_level = '江湖好手'
    else:
        work_level = work_level[:3]  # 取境界前3位，补全初期、中期、圆满任务可不取

    jsondata_ = reward()
    item_s = Items()
    yaocai_data = jsondata_.reward_yaocai_data()
    levelpricedata = jsondata_.reward_levelprice_data()
    ansha_data = jsondata_.reward_ansa_data()
    zuoyao_data = jsondata_.reward_zuoyao_data()

    # 部分高境界（如斩我境、遁一境、至尊等）在悬赏配置中没有独立任务档位，
    # 若当前境界不存在于配置，则自动降档到已配置的最高境界（通常为虚道境），避免 KeyError。
    if work_level not in yaocai_data:
        # 排除“江湖好手”，其单独处理
        higher_levels = [k for k in yaocai_data.keys() if k != "江湖好手"]
        if higher_levels:
            # 配置文件本身已按境界由低到高书写，直接取最后一个作为最高可用档位
            work_level = higher_levels[-1]

    work_json = {}
    work_list = [yaocai_data[work_level], ansha_data[work_level], zuoyao_data[work_level]]
    i = 1
    for w in work_list:
        work_name_list = []
        for k, v in w.items():
            work_name_list.append(k)
        work_name = random.choice(work_name_list)
        work_info = w[work_name]
        level_price_data = levelpricedata[work_level][work_info['level']]
        rate, isOut = countrate(exp, level_price_data["needexp"])
        success_msg = work_info['succeed']
        fail_msg = work_info['fail']
        item_type = get_random_item_type(is_superuser)
        item_type_for_api = ["法器", "防具"] if item_type[0] == "装备" else item_type
        item_id = item_s.get_random_id_list_by_rank_and_item_type(USERRANK[user_level], item_type_for_api)
        if not item_id:
            item_id = 0
        else:
            item_id = random.choice(item_id)
        base_time = int(level_price_data["time"] * isOut)
        extra_min = accept_count * 2  # 每次接取递增 次数*2 分钟
        work_json[work_name] = [rate, level_price_data["award"], base_time + extra_min, item_id,
                                success_msg, fail_msg]
        i += 1
    return work_json


def get_random_item_type(is_superuser=False):
    """随机物品类型。装备：其他人5%，超管20%；其余为功法/神通/药材均分。"""
    # 5% => 63/(1200+63)；20% => 300/(1200+300)
    equip_rate = 300 if is_superuser else 63
    type_rate = {
        "功法": {"type_rate": 400},
        "神通": {"type_rate": 400},
        "药材": {"type_rate": 400},
        "装备": {"type_rate": equip_rate},
    }
    temp_dict = {i: v["type_rate"] for i, v in type_rate.items()}
    key = [OtherSet().calculated(temp_dict)]
    return key


def countrate(exp, needexp):
    rate = int(exp / needexp * 100)
    isOut = 1
    if rate >= 100:
        tp = 1
        flag = True
        while flag:
            r = exp / needexp * 100
            if r > 100:
                tp += 1
                exp /= 1.5
            else:
                flag = False

        rate = 100
        isOut = float(1 - tp * 0.05)
        if isOut < 0.5:
            isOut = 0.5
    return rate, round(isOut, 2)
