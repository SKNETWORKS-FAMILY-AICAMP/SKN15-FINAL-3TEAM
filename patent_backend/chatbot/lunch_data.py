"""
점심 메뉴 데이터 및 추천 로직
"""
import random

# 점심 메뉴 데이터
LUNCH_MENU = {
    '한식': [
        '김치찌개', '된장찌개', '순두부찌개', '부대찌개',
        '비빔밥', '돌솥비빔밥', '제육볶음', '불고기',
        '삼겹살', '갈비탕', '설렁탕', '육개장',
        '냉면', '막국수', '칼국수', '된장백반'
    ],
    '중식': [
        '짜장면', '짬뽕', '탕수육', '볶음밥',
        '마파두부', '유산슬', '깐풍기', '라조기',
        '양장피', '삼선짬뽕', '사천짜장', '쟁반짜장'
    ],
    '일식': [
        '초밥', '회덮밥', '돈카츠', '우동',
        '라멘', '규동', '오야코동', '가츠동',
        '연어덮밥', '장어덮밥', '텐동', '소바'
    ],
    '양식': [
        '파스타', '피자', '스테이크', '리조또',
        '샐러드', '햄버거', '샌드위치', '오므라이스',
        '그라탕', '필라프', '까르보나라', '알리오올리오'
    ],
    '분식': [
        '떡볶이', '라면', '김밥', '순대',
        '튀김', '어묵', '쫄면', '비빔국수',
        '우동', '만두', '왕만두', '치즈떡볶이'
    ],
    '기타': [
        '샐러드', '포케', '월남쌈', '쌀국수',
        '카레', '돈부리', '타코', '부리또',
        '샤브샤브', '훠궈', '곱창', '족발'
    ]
}


def get_all_menu_items():
    """모든 메뉴 아이템을 평면 리스트로 반환"""
    all_items = []
    for category, items in LUNCH_MENU.items():
        all_items.extend(items)
    return all_items


def get_random_menu(count=1):
    """
    랜덤 메뉴 추천

    Args:
        count: 추천할 메뉴 개수 (기본 1개)

    Returns:
        추천 메뉴 리스트
    """
    all_menus = get_all_menu_items()
    return random.sample(all_menus, min(count, len(all_menus)))


def get_menu_by_category(category):
    """
    카테고리별 메뉴 반환

    Args:
        category: 메뉴 카테고리 (한식, 중식, 일식, 양식, 분식, 기타)

    Returns:
        해당 카테고리의 메뉴 리스트
    """
    return LUNCH_MENU.get(category, [])


def get_random_menu_by_category(category, count=1):
    """
    카테고리별 랜덤 메뉴 추천

    Args:
        category: 메뉴 카테고리
        count: 추천할 메뉴 개수

    Returns:
        추천 메뉴 리스트
    """
    menus = get_menu_by_category(category)
    if not menus:
        return []
    return random.sample(menus, min(count, len(menus)))
