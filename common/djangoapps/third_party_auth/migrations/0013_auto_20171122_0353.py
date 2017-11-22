# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0012_auto_20170626_1135'),
    ]

    operations = [
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='sync_learner_profile_data',
            field=models.BooleanField(default=False, help_text="Enforce a learner's edX profile data to synchronize with data received from the provider, in all SSO scenarios. The learner will always be notified if the email changes."),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='sync_learner_profile_data',
            field=models.BooleanField(default=False, help_text="Enforce a learner's edX profile data to synchronize with data received from the provider, in all SSO scenarios. The learner will always be notified if the email changes."),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='sync_learner_profile_data',
            field=models.BooleanField(default=False, help_text="Enforce a learner's edX profile data to synchronize with data received from the provider, in all SSO scenarios. The learner will always be notified if the email changes."),
        ),
    ]
