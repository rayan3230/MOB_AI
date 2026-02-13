from django.db import migrations, models


def clean_invalid_rack_ids(apps, schema_editor):
    Produit = apps.get_model('Produit', 'Produit')
    Rack = apps.get_model('warhouse', 'Rack')

    valid_rack_ids = set(Rack.objects.values_list('id_rack', flat=True))

    Produit.objects.filter(id_rack='').update(id_rack=None)

    if valid_rack_ids:
        Produit.objects.exclude(id_rack__isnull=True).exclude(id_rack__in=valid_rack_ids).update(id_rack=None)
    else:
        Produit.objects.update(id_rack=None)


class Migration(migrations.Migration):

    dependencies = [
        ('warhouse', '0013_alter_emplacement_id_emplacement_and_more'),
        ('Produit', '0005_produit_id_rack'),
    ]

    operations = [
        migrations.RunPython(clean_invalid_rack_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='produit',
            name='id_rack',
            field=models.ForeignKey(
                blank=True,
                db_column='id_rack',
                null=True,
                on_delete=models.SET_NULL,
                related_name='products',
                to='warhouse.rack',
                to_field='id_rack',
            ),
        ),
    ]
