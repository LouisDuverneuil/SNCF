# Generated by Django 3.2.8 on 2021-11-25 19:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0006_reservation_prix'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='place',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='website.place'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='reservation',
            unique_together={('trajet', 'place', 'confirmation')},
        ),
    ]
