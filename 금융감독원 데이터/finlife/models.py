from django.db import models


class DepositProducts(models.Model):
    fin_prdt_cd = models.CharField(max_length=100, unique=True)
    kor_co_nm = models.CharField(max_length=100)
    fin_prdt_nm = models.CharField(max_length=200)
    etc_note = models.TextField(blank=True)
    join_deny = models.IntegerField(null=True, blank=True)
    join_member = models.TextField(blank=True)
    join_way = models.TextField(blank=True)
    spcl_cnd = models.TextField(blank=True)

    def __str__(self):
        return f'{self.kor_co_nm} - {self.fin_prdt_nm}'


class DepositOptions(models.Model):
    product = models.ForeignKey(
        DepositProducts,
        on_delete=models.CASCADE,
        related_name='options'
    )
    fin_prdt_cd = models.CharField(max_length=100)
    intr_rate_type = models.CharField(max_length=20, blank=True)
    intr_rate_type_nm = models.CharField(max_length=100, blank=True)
    save_trm = models.IntegerField()
    intr_rate = models.FloatField(default=-1)
    intr_rate2 = models.FloatField(default=-1)

    def __str__(self):
        return f'{self.fin_prdt_cd} - {self.save_trm}개월 - 최고 {self.intr_rate2}%'