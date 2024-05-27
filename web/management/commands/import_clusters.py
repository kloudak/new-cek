import csv
from django.core.management.base import BaseCommand
from web.models import Clustering, Cluster, PoemInCluster, Poem, PoemInCCV

class Command(BaseCommand):
    help = 'Import clusters and their related data from CSV files'

    def add_arguments(self, parser):
        parser.add_argument('clustering_id', type=int, help='ID of the clustering to import')

    def handle(self, *args, **options):
        data_dir = "web/data/clustering/"
        clustering_id = options['clustering_id']
        self.stdout.write(self.style.SUCCESS(f'Importing data for clustering ID {clustering_id}'))

        # Step 1: Import Clustering from clustering.csv
        with open(f'{data_dir}clustering.csv', mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if int(row['id']) == clustering_id:
                    clustering, created = Clustering.objects.update_or_create(
                        id=row['id'],
                        defaults={'name': row['name'], 'description': row['description']}
                    )
                    self.stdout.write(self.style.SUCCESS(f'Successfully imported Clustering: {clustering.name}'))
                    break

        # Step 2: Import Clusters from cluster.csv
        cluster_ids = []
        with open(f'{data_dir}cluster.csv', mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if int(row['id_clustering']) == clustering_id:
                    cluster_ids.append(row['id'])
                    cluster, created = Cluster.objects.update_or_create(
                        id=row['id'],
                        defaults={
                            'clustering_id': row['id_clustering'],
                            'name': row['name'],
                            'description': row['description'],
                            'number_of_documents': row['n_documents']
                        }
                    )
                    self.stdout.write(self.style.SUCCESS(f'Successfully imported Cluster: {cluster.id}'))
        
        # Step 3: Import PoemInClusters from cluster_poem.csv
        #id_mapping = {}
        #for pic in PoemInCCV.objects.exclude(poem_in_cek__isnull=True):
        #    id_mapping[pic.cluster_id] = pic.poem_in_cek.id
        
        with open(f'{data_dir}cluster_poem.csv', mode='r') as file:
            reader = csv.DictReader(file)
            row_idx = 1
            for row in reader:
                if not row['id_cluster'] in cluster_ids:
                    continue
                if row_idx % 1000 == 0:
                    self.stdout.write(self.style.SUCCESS(f'Processing row {row_idx}'))
                row_idx += 1
                cluster = Cluster.objects.filter(id=row['id_cluster']).first()
                try:
                    poem = PoemInCCV.objects.get(cluster_id=row['id_poem']).poem_in_cek
                    pic, created = PoemInCluster.objects.update_or_create(
                        poem=poem,
                        cluster=cluster,
                        score = row['score']
                    )
                except:
                    self.stdout.write(self.style.ERROR(f"Poem with old id {row['id_poem']} not found!"))