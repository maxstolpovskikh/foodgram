# Generated by Django 4.2.16 on 2024-11-25 17:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_subscription_subscription_unique_subscription'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subscription',
            options={'ordering': ('author',), 'verbose_name': 'Подписка', 'verbose_name_plural': 'Подписки'},
        ),
    ]