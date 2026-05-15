import requests
from django.conf import settings


FSS_DEPOSIT_API_URL = 'http://finlife.fss.or.kr/finlifeapi/depositProductsSearch.json'


def fetch_deposit_products():
    params = {
        'auth': settings.FSS_API_KEY,
        'topFinGrpNo': '020000',
        'pageNo': 1,
    }

    response = requests.get(FSS_DEPOSIT_API_URL, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    result = data.get('result', {})

    return {
        'products': result.get('baseList', []),
        'options': result.get('optionList', []),
    }


def normalize_rate(value):
    if value is None or value == '':
        return -1
    return float(value)