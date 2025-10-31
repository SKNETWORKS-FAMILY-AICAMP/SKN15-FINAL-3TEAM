"""
점심 추천 데이터 - 이스터에그 기능
각 카테고리별 대표 메뉴 10개씩
"""

LUNCH_MENU = {
    "한식": [
        {
            "name": "김치찌개",
            "description": "얼큰하고 매콤한 김치와 돼지고기의 조화, 따뜻한 국물 요리"
        },
        {
            "name": "된장찌개",
            "description": "구수하고 담백한 된장 베이스의 건강한 찌개"
        },
        {
            "name": "비빔밥",
            "description": "다양한 나물과 고추장을 비벼먹는 영양 만점 한 그릇 요리"
        },
        {
            "name": "불고기",
            "description": "달콤하게 양념한 소고기를 구워낸 한국 대표 고기 요리"
        },
        {
            "name": "삼겹살",
            "description": "고소하고 담백한 돼지 삼겹살 구이"
        },
        {
            "name": "냉면",
            "description": "시원하고 개운한 국물의 차가운 면 요리"
        },
        {
            "name": "떡볶이",
            "description": "쫄깃한 떡과 매콤달콤한 고추장 소스의 길거리 음식"
        },
        {
            "name": "순두부찌개",
            "description": "부드러운 순두부와 해물이 들어간 얼큰한 찌개"
        },
        {
            "name": "제육볶음",
            "description": "매콤하게 양념한 돼지고기 볶음 요리"
        },
        {
            "name": "갈비탕",
            "description": "소갈비를 푹 고아 만든 깊은 맛의 보양 국물 요리"
        }
    ],
    "중식": [
        {
            "name": "짜장면",
            "description": "달콤한 춘장 소스에 면을 비벼먹는 중화 요리"
        },
        {
            "name": "짬뽕",
            "description": "얼큰하고 시원한 해물 국물의 매운 면 요리"
        },
        {
            "name": "탕수육",
            "description": "바삭한 튀김옷과 새콤달콤한 소스의 돼지고기 요리"
        },
        {
            "name": "마파두부",
            "description": "매콤하고 얼얼한 두부 요리, 밥과 잘 어울림"
        },
        {
            "name": "양장피",
            "description": "쫄깃한 전분피에 다양한 해물과 채소를 올린 차가운 요리"
        },
        {
            "name": "깐풍기",
            "description": "바삭한 닭튀김에 매콤달콤한 소스를 버무린 요리"
        },
        {
            "name": "유산슬",
            "description": "각종 해산물과 야채를 볶은 고급 중화 요리"
        },
        {
            "name": "볶음밥",
            "description": "고슬고슬한 밥에 계란과 야채를 볶아낸 간단한 요리"
        },
        {
            "name": "팔보채",
            "description": "여덟 가지 재료를 볶아낸 풍성한 중화 볶음 요리"
        },
        {
            "name": "고추잡채",
            "description": "당면과 야채를 볶은 매콤한 중화 요리"
        }
    ],
    "일식": [
        {
            "name": "초밥",
            "description": "신선한 생선회를 밥 위에 올린 일본 전통 요리"
        },
        {
            "name": "라멘",
            "description": "진한 국물과 쫄깃한 면이 어우러진 일본식 국수"
        },
        {
            "name": "돈카츠",
            "description": "바삭한 튀김옷의 두툼한 돼지고기 커틀릿"
        },
        {
            "name": "우동",
            "description": "쫄깃한 굵은 면과 담백한 국물의 면 요리"
        },
        {
            "name": "규동",
            "description": "달콤짭짤하게 조린 소고기를 밥 위에 올린 덮밥"
        },
        {
            "name": "카레라이스",
            "description": "고소하고 부드러운 일본식 카레와 밥"
        },
        {
            "name": "오야코동",
            "description": "닭고기와 계란을 달콤하게 조려 밥 위에 올린 덮밥"
        },
        {
            "name": "텐동",
            "description": "바삭한 새우 튀김을 간장 소스에 얹은 덮밥"
        },
        {
            "name": "회덮밥",
            "description": "신선한 회와 야채를 매콤달콤한 소스에 비빈 덮밥"
        },
        {
            "name": "나베",
            "description": "각종 해물과 야채를 넣고 끓인 따뜻한 전골 요리"
        }
    ],
    "양식": [
        {
            "name": "스테이크",
            "description": "두툼한 소고기를 구워낸 고급 육류 요리"
        },
        {
            "name": "파스타",
            "description": "다양한 소스와 면이 어우러진 이탈리아 면 요리"
        },
        {
            "name": "피자",
            "description": "바삭한 도우 위에 치즈와 토핑을 올린 이탈리아 요리"
        },
        {
            "name": "리조또",
            "description": "크리미한 치즈와 쌀을 볶아낸 이탈리아 쌀 요리"
        },
        {
            "name": "햄버거",
            "description": "두툼한 패티와 신선한 야채가 들어간 미국식 샌드위치"
        },
        {
            "name": "샐러드",
            "description": "신선한 채소와 드레싱의 건강한 한 끼"
        },
        {
            "name": "그라탕",
            "description": "치즈를 듬뿍 올려 오븐에 구운 따뜻한 요리"
        },
        {
            "name": "샌드위치",
            "description": "빵 사이에 다양한 재료를 넣은 간편한 식사"
        },
        {
            "name": "오므라이스",
            "description": "부드러운 계란으로 감싼 볶음밥 요리"
        },
        {
            "name": "쉬림프 크림파스타",
            "description": "새우와 크림 소스가 어우러진 부드러운 파스타"
        }
    ]
}


def get_all_menu_items():
    """모든 메뉴 아이템을 하나의 리스트로 반환"""
    all_items = []
    for category, items in LUNCH_MENU.items():
        for item in items:
            all_items.append({
                "category": category,
                "name": item["name"],
                "description": item["description"]
            })
    return all_items


def get_menu_by_category(category: str):
    """특정 카테고리의 메뉴 반환"""
    return LUNCH_MENU.get(category, [])


def get_random_menu(category: str = None):
    """랜덤 메뉴 추천 (카테고리 지정 가능)"""
    import random

    if category and category in LUNCH_MENU:
        menu = random.choice(LUNCH_MENU[category])
        return {
            "category": category,
            "name": menu["name"],
            "description": menu["description"]
        }
    else:
        # 전체 메뉴에서 랜덤 선택
        category = random.choice(list(LUNCH_MENU.keys()))
        menu = random.choice(LUNCH_MENU[category])
        return {
            "category": category,
            "name": menu["name"],
            "description": menu["description"]
        }
