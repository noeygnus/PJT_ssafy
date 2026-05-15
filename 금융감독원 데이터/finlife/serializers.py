from rest_framework import serializers
from .models import DepositProducts, DepositOptions


class DepositOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositOptions
        fields = [
            'id',
            'fin_prdt_cd',
            'intr_rate_type',
            'intr_rate_type_nm',
            'save_trm',
            'intr_rate',
            'intr_rate2',
        ]


class DepositProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositProducts
        fields = [
            'id',
            'fin_prdt_cd',
            'kor_co_nm',
            'fin_prdt_nm',
            'etc_note',
            'join_deny',
            'join_member',
            'join_way',
            'spcl_cnd',
        ]


class DepositProductDetailSerializer(serializers.ModelSerializer):
    options = DepositOptionsSerializer(many=True, read_only=True)

    class Meta:
        model = DepositProducts
        fields = [
            'id',
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