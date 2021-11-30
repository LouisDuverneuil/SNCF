# Generated by Django 3.2.8 on 2021-11-30 14:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0010_reservation_date'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='reservation',
            name='billet',
        ),
        migrations.AlterUniqueTogether(
            name='reservation',
            unique_together={('trajet', 'place')},
        ),
        migrations.RemoveField(
            model_name='reservation',
            name='confirmation',
        ),
    ]
