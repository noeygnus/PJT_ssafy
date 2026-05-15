import json
from pathlib import Path
from django.conf import settings

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import DepositProducts, DepositOptions
from .serializers import (
    DepositProductsSerializer,
    DepositOptionsSerializer,
    DepositProductDetailSerializer,
)
from .services.fss_client import fetch_deposit_products, normalize_rate
from .services.dummy_generator import generate_dummy_deposit_data
from .services.validator import validate_dummy_data


@api_view(['GET'])
def save_deposit_products(request):
    data = fetch_deposit_products()

    products = data['products']
    options = data['options']

    for item in products:
        DepositProducts.objects.update_or_create(
            fin_prdt_cd=item.get('fin_prdt_cd'),
            defaults={
                'kor_co_nm': item.get('kor_co_nm', ''),
                'fin_prdt_nm': item.get('fin_prdt_nm', ''),
                'etc_note': item.get('etc_note', ''),
                'join_deny': item.get('join_deny'),
                'join_member': item.get('join_member', ''),
                'join_way': item.get('join_way', ''),
                'spcl_cnd': item.get('spcl_cnd', ''),
            }
        )

    for item in options:
        fin_prdt_cd = item.get('fin_prdt_cd')

        try:
            product = DepositProducts.objects.get(fin_prdt_cd=fin_prdt_cd)
        except DepositProducts.DoesNotExist:
            continue

        DepositOptions.objects.update_or_create(
            product=product,
            fin_prdt_cd=fin_prdt_cd,
            intr_rate_type=item.get('intr_rate_type', ''),
            save_trm=int(item.get('save_trm')),
            defaults={
                'intr_rate_type_nm': item.get('intr_rate_type_nm', ''),
                'intr_rate': normalize_rate(item.get('intr_rate')),
                'intr_rate2': normalize_rate(item.get('intr_rate2')),
            }
        )

    return Response({'message': 'okay'})


@api_view(['GET', 'POST'])
def deposit_products(request):
    if request.method == 'GET':
        products = DepositProducts.objects.all()
        serializer = DepositProductsSerializer(products, many=True)
        return Response(serializer.data)

    serializer = DepositProductsSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': '데이터 삽입 성공', 'data': serializer.data},
            status=status.HTTP_201_CREATED
        )

    return Response(
        {'message': '데이터 삽입 실패', 'errors': serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
def deposit_product_options(request, fin_prdt_cd):
    options = DepositOptions.objects.filter(fin_prdt_cd=fin_prdt_cd)

    if not options.exists():
        return Response(
            {'message': '해당 상품의 옵션 정보가 없습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = DepositOptionsSerializer(options, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def top_rate(request):
    option = DepositOptions.objects.order_by('-intr_rate2').first()

    if option is None:
        return Response(
            {'message': '저장된 옵션 데이터가 없습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )

    product_serializer = DepositProductsSerializer(option.product)
    option_serializer = DepositOptionsSerializer(option)

    return Response({
        'product': product_serializer.data,
        'option': option_serializer.data,
    })


@api_view(['GET'])
def deposit_product_detail(request, fin_prdt_cd):
    try:
        product = DepositProducts.objects.get(fin_prdt_cd=fin_prdt_cd)
    except DepositProducts.DoesNotExist:
        return Response(
            {'message': '해당 상품이 존재하지 않습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = DepositProductDetailSerializer(product)
    return Response(serializer.data)


@api_view(['POST'])
def generate_dummy_data(request):
    count = request.data.get('count', 10)

    try:
        count = int(count)
    except ValueError:
        return Response(
            {'message': 'count는 숫자여야 합니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        dummy_data = generate_dummy_deposit_data(count=count)
        is_valid, errors = validate_dummy_data(dummy_data)

        if not is_valid:
            return Response(
                {
                    'message': '더미 데이터 검증 실패',
                    'errors': errors,
                    'data': dummy_data,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        output_path = Path(settings.BASE_DIR) / 'dummy_data.json'

        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(dummy_data, file, ensure_ascii=False, indent=2)

        return Response(
            {
                'message': '더미 데이터 생성 성공',
                'count': len(dummy_data),
                'file': 'dummy_data.json',
                'data': dummy_data,
            },
            status=status.HTTP_201_CREATED
        )

    except Exception as error:
        return Response(
            {
                'message': '더미 데이터 생성 실패',
                'error': str(error),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )