REQUIRED_PRODUCT_FIELDS = [
    'fin_prdt_cd',
    'kor_co_nm',
    'fin_prdt_nm',
    'etc_note',
    'join_deny',
    'join_member',
    'join_way',
    'spcl_cnd',
    'options',
]

REQUIRED_OPTION_FIELDS = [
    'intr_rate_type',
    'intr_rate_type_nm',
    'save_trm',
    'intr_rate',
    'intr_rate2',
]


def validate_dummy_data(data):
    errors = []

    if not isinstance(data, list):
        return False, ['최상위 데이터는 list여야 합니다.']

    product_codes = set()

    for product_index, product in enumerate(data):
        if not isinstance(product, dict):
            errors.append(f'{product_index}번째 상품은 object여야 합니다.')
            continue

        for field in REQUIRED_PRODUCT_FIELDS:
            if field not in product:
                errors.append(f'{product_index}번째 상품에 {field} 필드가 없습니다.')

        fin_prdt_cd = product.get('fin_prdt_cd')
        if fin_prdt_cd in product_codes:
            errors.append(f'중복 상품 코드가 있습니다: {fin_prdt_cd}')
        product_codes.add(fin_prdt_cd)

        if not isinstance(product.get('join_deny'), int):
            errors.append(f'{fin_prdt_cd}의 join_deny는 int여야 합니다.')

        options = product.get('options')
        if not isinstance(options, list) or len(options) == 0:
            errors.append(f'{fin_prdt_cd}의 options는 비어 있지 않은 list여야 합니다.')
            continue

        option_keys = set()

        for option_index, option in enumerate(options):
            if not isinstance(option, dict):
                errors.append(f'{fin_prdt_cd}의 {option_index}번째 옵션은 object여야 합니다.')
                continue

            for field in REQUIRED_OPTION_FIELDS:
                if field not in option:
                    errors.append(f'{fin_prdt_cd}의 {option_index}번째 옵션에 {field} 필드가 없습니다.')

            save_trm = option.get('save_trm')
            intr_rate = option.get('intr_rate')
            intr_rate2 = option.get('intr_rate2')

            if not isinstance(save_trm, int):
                errors.append(f'{fin_prdt_cd} 옵션의 save_trm은 int여야 합니다.')

            if not isinstance(intr_rate, (int, float)):
                errors.append(f'{fin_prdt_cd} 옵션의 intr_rate는 숫자여야 합니다.')

            if not isinstance(intr_rate2, (int, float)):
                errors.append(f'{fin_prdt_cd} 옵션의 intr_rate2는 숫자여야 합니다.')

            if isinstance(intr_rate, (int, float)) and isinstance(intr_rate2, (int, float)):
                if intr_rate2 < intr_rate:
                    errors.append(f'{fin_prdt_cd} 옵션의 intr_rate2가 intr_rate보다 작습니다.')

                if not (1.5 <= intr_rate <= 5.5):
                    errors.append(f'{fin_prdt_cd} 옵션의 intr_rate가 허용 범위를 벗어났습니다.')

                if not (1.5 <= intr_rate2 <= 5.5):
                    errors.append(f'{fin_prdt_cd} 옵션의 intr_rate2가 허용 범위를 벗어났습니다.')

            option_key = (
                option.get('intr_rate_type'),
                option.get('save_trm'),
            )

            if option_key in option_keys:
                errors.append(f'{fin_prdt_cd}에 중복 옵션이 있습니다: {option_key}')
            option_keys.add(option_key)

    return len(errors) == 0, errors