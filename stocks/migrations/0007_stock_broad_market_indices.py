# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-29 17:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0006_auto_20170512_1159'),
    ]

    operations = [
        migrations.AddField(
            model_name='stock',
            name='broad_market_indices',
            field=models.PositiveSmallIntegerField(blank=True, choices=[(0, 'Nifty 50'), (1, 'Nifty Next 50'), (2, 'Nifty Midcap')], null=True),
        ),
    ]