# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        ('entitlements', '0002_auto_20171102_0719'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseEntitlementPolicy',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('expiration_period_days', models.IntegerField(default=450, help_text=b'Number of days from when an entitlement is created until when it is expired.')),
                ('refund_period_days', models.IntegerField(default=60, help_text=b'Number of days from when an entitlement is created until when it is no longer refundable.')),
                ('regain_period_days', models.IntegerField(default=14, help_text=b'Number of days from when an entitlement is created until when it is no longer able to be regained by a user.')),
                ('site', models.ForeignKey(to='sites.Site')),
            ],
        ),
        migrations.AddField(
            model_name='courseentitlement',
            name='policy',
            field=models.ForeignKey(to='entitlements.CourseEntitlementPolicy', null=True),
        ),
    ]
