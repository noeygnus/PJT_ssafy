import json
import re
import requests
from django.conf import settings


UPSTAGE_CHAT_API_URL = 'https://api.upstage.ai/v1/solar/chat/completions'


def extract_json_array(text):
    """
    LLM 응답에서 JSON 배열만 안전하게 추출한다.
    """
    text = text.strip()

    if text.startswith('```'):
        text = re.sub(r'^```json', '', text)
        text = re.sub(r'^```', '', text)
        text = re.sub(r'```$', '', text)
        text = text.strip()

    start = text.find('[')
    end = text.rfind(']')

    if start == -1 or end == -1:
        raise ValueError('응답에서 JSON 배열을 찾을 수 없습니다.')

    return text[start:end + 1]


def generate_dummy_deposit_data(count=10):
    if not settings.UPSTAGE_API_KEY:
        raise ValueError('UPSTAGE_API_KEY가 설정되어 있지 않습니다.')

    system_prompt = """
당신은 금융상품 더미 데이터를 생성하는 데이터 엔지니어입니다.
반드시 JSON 배열만 반환하세요.
마크다운, 설명, 주석은 절대 포함하지 마세요.
"""

    user_prompt = f"""
정기예금 상품 더미 데이터 {count}개를 생성하세요.

각 데이터는 아래 구조를 정확히 따라야 합니다.

[
  {{
    "fin_prdt_cd": "DUMMY001",
    "kor_co_nm": "예시은행",
    "fin_prdt_nm": "예시 정기예금",
    "etc_note": "상품 유의사항",
    "join_deny": 1,
    "join_member": "실명의 개인",
    "join_way": "영업점, 인터넷, 스마트폰",
    "spcl_cnd": "우대 조건",
    "options": [
      {{
        "intr_rate_type": "S",
        "intr_rate_type_nm": "단리",
        "save_trm": 6,
        "intr_rate": 3.1,
        "intr_rate2": 3.4
      }}
    ]
  }}
]

생성 규칙:
- fin_prdt_cd는 반드시 중복되지 않아야 합니다.
- kor_co_nm은 실제 은행처럼 자연스러운 이름이어야 합니다.
- join_deny는 1, 2, 3 중 하나입니다.
- options는 상품마다 2~4개 생성하세요.
- save_trm은 6, 12, 24, 36 중 하나입니다.
- intr_rate와 intr_rate2는 숫자 타입이어야 합니다.
- intr_rate2는 intr_rate보다 크거나 같아야 합니다.
- 금리는 1.5 이상 5.5 이하 범위로 생성하세요.
- JSON 배열 외의 텍스트는 절대 반환하지 마세요.
"""

    payload = {
        'model': 'solar-pro3',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'temperature': 0.4,
        'max_tokens': 4000,
        'stream': False,
    }

    headers = {
        'Authorization': f'Bearer {settings.UPSTAGE_API_KEY}',
        'Content-Type': 'application/json',
    }

    response = requests.post(
        UPSTAGE_CHAT_API_URL,
        headers=headers,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()

    result = response.json()
    content = result['choices'][0]['message']['content']

    json_text = extract_json_array(content)
    return json.loads(json_text)