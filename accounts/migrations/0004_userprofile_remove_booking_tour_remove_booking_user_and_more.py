# Generated by Django 5.2 on 2025-05-15 16:30

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_tour_created_at_tour_description_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('tourist', 'Tourist'), ('operator', 'Tour Operator'), ('admin', 'Administrator')], default='tourist', max_length=20)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='profile_pics/')),
                ('bio', models.TextField(blank=True, null=True)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RemoveField(
            model_name='booking',
            name='tour',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='user',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='booking',
        ),
        migrations.DeleteModel(
            name='Report',
        ),
        migrations.RemoveField(
            model_name='review',
            name='tour',
        ),
        migrations.RemoveField(
            model_name='review',
            name='user',
        ),
        migrations.DeleteModel(
            name='Booking',
        ),
        migrations.DeleteModel(
            name='Payment',
        ),
        migrations.DeleteModel(
            name='Tour',
        ),
        migrations.DeleteModel(
            name='Review',
        ),
    ]
