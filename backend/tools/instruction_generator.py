"""指令生成器 — 根据战术风格和阵容生成球队+个人指令"""

import json
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class InstructionGenerator:
    """指令生成器"""

    def __init__(self):
        with open(DATA_DIR / "styles.json", "r", encoding="utf-8") as f:
            self.styles = json.load(f)["styles"]

    def generate(
        self,
        style: str,
        formation: str,
        assignments: list[dict],
    ) -> dict:
        """
        生成完整的战术指令

        返回:
            {
                "mentality": "attacking",
                "team_instructions": {...},
                "player_instructions": [{slot, player, individual_instructions}, ...],
                "set_piece_routines": {...},
            }
        """
        style_data = self.styles.get(style, self.styles["gegenpress"])

        return {
            "style_name": style_data.get("label_zh", style),
            "style_description": style_data.get("description_zh", ""),
            "mentality": style_data.get("mentality", "balanced"),
            "team_instructions": style_data.get("instructions", {}),
            "player_instructions": self._generate_player_instructions(assignments, style),
            "set_piece_routines": self._generate_set_pieces(assignments),
            "key_principles": self._generate_principles(style, assignments),
        }

    def _generate_player_instructions(self, assignments: list[dict], style: str) -> list[dict]:
        """生成个人指令"""
        instructions = []

        # 角色→个人指令映射
        role_instructions_map = {
            "SK_A": ["more_risky_passes", "dribble_more"],
            "SK_S": ["take_short_kicks", "distribute_to_centre_backs"],
            "SK_D": ["take_short_kicks", "fewer_risky_passes"],
            "BPD_D": ["more_direct_passes", "dribble_more"],
            "BPD_S": ["more_direct_passes", "dribble_more"],
            "FB_A": ["stay_wider", "cross_more_often", "get_forward"],
            "FB_S": ["stay_wider", "cross_from_deep"],
            "FB_D": ["hold_position", "fewer_risky_passes"],
            "WB_A": ["stay_wider", "cross_more_often", "get_forward", "dribble_more"],
            "WB_S": ["stay_wider", "cross_more_often"],
            "CWB_A": ["stay_wider", "cross_more_often", "dribble_more", "roam_from_position", "get_forward"],
            "IWB_A": ["sit_narrower", "cut_inside_with_ball", "get_forward"],
            "IWB_S": ["sit_narrower", "cut_inside_with_ball"],
            "DM_D": ["hold_position", "fewer_risky_passes", "tackle_harder"],
            "DM_S": ["hold_position"],
            "DLP_D": ["more_direct_passes", "hold_position"],
            "DLP_S": ["more_risky_passes"],
            "A_D": ["hold_position", "fewer_risky_passes"],
            "HB_D": ["hold_position", "fewer_risky_passes"],
            "RGA_S": ["more_risky_passes", "more_direct_passes", "roam_from_position"],
            "VOL_A": ["get_forward", "dribble_more", "move_into_channels"],
            "BWM_D": ["tackle_harder", "hold_position", "mark_tighter"],
            "BWM_S": ["tackle_harder", "mark_tighter"],
            "CM_A": ["get_forward", "dribble_more", "more_risky_passes", "move_into_channels"],
            "CM_S": ["shoot_less_often"],
            "CM_D": ["hold_position", "fewer_risky_passes"],
            "BBM_S": ["get_forward", "roam_from_position", "move_into_channels"],
            "AP_A": ["more_risky_passes", "roam_from_position", "dribble_more"],
            "AP_S": ["more_risky_passes", "roam_from_position"],
            "MEZ_A": ["get_forward", "dribble_more", "stay_wider", "move_into_channels"],
            "MEZ_S": ["stay_wider", "move_into_channels"],
            "CAR_S": ["stay_wider", "hold_position"],
            "W_A": ["stay_wider", "cross_more_often", "dribble_more", "get_forward"],
            "W_S": ["stay_wider", "cross_more_often"],
            "IF_A": ["sit_narrower", "cut_inside_with_ball", "get_forward", "dribble_more"],
            "IF_S": ["sit_narrower", "cut_inside_with_ball", "shoot_less_often"],
            "IW_A": ["sit_narrower", "cut_inside_with_ball", "get_forward", "dribble_more"],
            "IW_S": ["sit_narrower", "cut_inside_with_ball"],
            "RMD_A": ["roam_from_position", "get_forward", "dribble_more"],
            "DW_S": ["stay_wider", "tackle_harder", "mark_tighter"],
            "SS_A": ["get_forward", "dribble_more", "move_into_channels"],
            "T_A": ["roam_from_position", "dribble_more", "more_risky_passes"],
            "EG_A": ["hold_position", "more_risky_passes"],
            "AF_A": ["dribble_more", "move_into_channels"],
            "P_A": ["dribble_more"],
            "DLF_A": ["hold_up_ball", "more_risky_passes", "move_into_channels"],
            "DLF_S": ["hold_up_ball", "more_risky_passes", "shoot_less_often"],
            "TF_A": ["hold_up_ball"],
            "TF_S": ["hold_up_ball", "shoot_less_often"],
            "CF_A": ["roam_from_position", "dribble_more", "move_into_channels"],
            "CF_S": ["roam_from_position", "hold_up_ball", "more_risky_passes"],
            "PF_A": ["tackle_harder", "mark_tighter", "dribble_more"],
            "PF_S": ["tackle_harder", "mark_tighter"],
            "F9_S": ["roam_from_position", "more_risky_passes", "dribble_more"],
        }

        instructions_labels = {
            "stay_wider": {"zh": "拉边", "en": "Stay Wider"},
            "sit_narrower": {"zh": "内收", "en": "Sit Narrower"},
            "cross_more_often": {"zh": "更多传中", "en": "Cross More Often"},
            "cross_from_deep": {"zh": "45度传中", "en": "Cross From Deep"},
            "dribble_more": {"zh": "更多盘带", "en": "Dribble More"},
            "get_forward": {"zh": "前插", "en": "Get Forward"},
            "hold_position": {"zh": "坚守位置", "en": "Hold Position"},
            "more_risky_passes": {"zh": "更多直塞", "en": "More Risky Passes"},
            "fewer_risky_passes": {"zh": "减少直塞", "en": "Fewer Risky Passes"},
            "more_direct_passes": {"zh": "更多直传", "en": "More Direct Passes"},
            "take_short_kicks": {"zh": "短传出球", "en": "Take Short Kicks"},
            "distribute_to_centre_backs": {"zh": "传给中卫", "en": "Distribute to CBs"},
            "roam_from_position": {"zh": "灵活跑位", "en": "Roam From Position"},
            "move_into_channels": {"zh": "拉边接应", "en": "Move Into Channels"},
            "cut_inside_with_ball": {"zh": "内切", "en": "Cut Inside With Ball"},
            "hold_up_ball": {"zh": "背身拿球", "en": "Hold Up Ball"},
            "shoot_less_often": {"zh": "减少射门", "en": "Shoot Less Often"},
            "tackle_harder": {"zh": "凶狠抢断", "en": "Tackle Harder"},
            "mark_tighter": {"zh": "贴身盯防", "en": "Mark Tighter"},
        }

        for slot in assignments:
            role_key = slot.get("role_key", "")
            player = slot.get("player", "")
            default_instructions = role_instructions_map.get(role_key, [])

            # 高压迫风格额外指令
            if style in ("gegenpress", "vertical_tiki_taka"):
                if not any(pi.startswith("tackle_") or pi.startswith("mark_") for pi in default_instructions):
                    default_instructions.append("mark_tighter")

            instructions.append({
                "slot": slot["slot"],
                "player": player,
                "role": slot.get("role", ""),
                "individual_instructions": [
                    instructions_labels.get(pi, {"zh": pi, "en": pi})
                    for pi in default_instructions
                ],
            })

        return instructions

    def _generate_set_pieces(self, assignments: list[dict]) -> dict:
        """生成定位球策略"""
        return {
            "corners": {
                "delivery": "mixed",
                "aim": "far_post",
                "instructions_zh": "角球混合传中，瞄准后门柱。让弹跳最好的球员攻击后点。",
            },
            "free_kicks": {
                "delivery": "best_judgement",
                "instructions_zh": "任意球由主罚者自行判断，传中或直接射门。",
            },
            "throw_ins": {
                "routine": "long_flat",
                "instructions_zh": "界外球尽量掷远掷平，寻求快速进攻机会。",
            },
            "penalties": {
                "taker": "best_penalty_taker",
                "instructions_zh": "点球由全队 Penalty Taking 最高的球员主罚。",
            },
        }

    def _generate_principles(self, style: str, assignments: list[dict]) -> list[str]:
        """生成核心战术原则"""
        style_principles = {
            "gegenpress": [
                "失球后立即反抢（5秒规则）",
                "高位防线配合越位陷阱",
                "边后卫大幅助攻，中场覆盖空间",
                "快速纵向传球，减少横向倒脚",
                "定位球是重要得分手段",
            ],
            "tiki_taka": [
                "耐心控球寻找空间",
                "短传为主，保持球权",
                "阵型紧凑，传球三角随时形成",
                "高位防守，压缩对手空间",
                "控球是最好的防守",
            ],
            "direct_counter": [
                "稳固防守优先，保持阵型",
                "得球后快速反击，3-4脚传球完成射门",
                "利用前锋速度打对方身后",
                "中场以拦截和分球为主",
                "定位球和传中是重要进攻手段",
            ],
            "wing_play": [
                "拉开宽度，创造一对一机会",
                "边后卫套边助攻",
                "高质量传中是最重要武器",
                "中路球员抢点包抄",
                "定位球有很大优势",
            ],
            "possession_flexible": [
                "控球与渗透相结合",
                "球员灵活换位制造混乱",
                "攻守平衡，不冒险",
                "根据比赛进程调整节奏",
                "给予创造性球员自由度",
            ],
            "vertical_tiki_taka": [
                "控球为基础，但追求纵向穿透",
                "积极反抢，高位压迫",
                "中路短传配合为主",
                "创造空间后立即传球穿透",
                "全队参与攻防",
            ],
            "fluid_counter": [
                "弹性防守，不盲目压迫",
                "抓对手失误快速反击",
                "保持阵型紧凑",
                "球员自由发挥空间大",
                "边中结合，不拘一格",
            ],
            "park_the_bus": [
                "全员防守，压缩纵深空间",
                "限制对手进入危险区域",
                "快速反击是唯一进攻手段",
                "定位球防守是生命线",
                "拖延时间，破坏比赛节奏",
            ],
        }

        return style_principles.get(style, style_principles["gegenpress"])
