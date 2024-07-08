from django.core.management.base import BaseCommand, CommandError
from web.models import Poem, PoemInCluster, PoemInCCV
import numpy as np
import pandas as pd
import os, glob, json


def find_poem_and_cluster_by_ccv_id(ccv_id, book_id):
    poem_in_ccv = (
        PoemInCCV.objects.filter(ccv_id=ccv_id).filter(book_in_cek__id=book_id).all()
    )
    if len(poem_in_ccv) != 1:
        print(f"Poem not found: {book_id} {ccv_id}.")
        return None, None
    poem_in_ccv = poem_in_ccv[0]
    if not poem_in_ccv is None:
        poem_id = poem_in_ccv.poem_in_cek.id
        cluster_id = (
            PoemInCluster.objects.filter(poem_id=poem_id)
            .values_list("cluster_id", flat=True)
            .first()
        )

        return poem_id, cluster_id
    else:
        print(f"Poem not found: {book_id} {ccv_id}.")
        print(ccv_id, book_id)
        return None, None

class Command(BaseCommand):
    help = "Go throught all poems with an embedding and find most similar poems within the same cluster."

    def handle(self, *args, **options):
        output_dir = "web/data/embeddings/clusters"
        
        if os.path.exists("web/data/embeddings/similar_poems.json"):
            poems = json.load(open("web/data/embeddings/similar_poems.json"))
            k = 0
            for pid, similar_poems in poems.items():
                k += 1
                if k % 1000 == 0:
                    self.stdout.write(self.style.SUCCESS(f"Processing {k}th poem."))
                poem = Poem.objects.get(id=int(pid))
                poem.similar_poems = json.dumps(similar_poems)
                poem.save()
            pass
        elif glob.glob(os.path.join(output_dir, "*.csv")):
            poems_with_cluster = Poem.objects.filter(
                cluster_membership__isnull=False
            ).select_related("cluster_membership")
            similar_poems = {}
            k = 0
            for poem in poems_with_cluster:
                k+=1
                if k % 1000 == 0:
                    self.stdout.write(self.style.SUCCESS(f"Processing {k}th poem."))
                pid = poem.id
                cluster_id = poem.cluster_membership.cluster_id
                distance_matrix_file = os.path.join(
                    output_dir, f"cluster_{cluster_id}_distances.csv"
                )
                if not os.path.exists(distance_matrix_file):
                    print(f"Distance matrix file for cluster {cluster_id} not found.")
                    continue

                distance_df = pd.read_csv(distance_matrix_file, index_col=0)

                # Get the distances for the current poem
                if pid not in distance_df.index:
                    print(
                        f"PID {pid} not found in distance matrix for cluster {cluster_id}."
                    )
                    continue
                distances = distance_df.loc[pid, :].sort_values()

                # Exclude the poem itself and get the 10 nearest poems
                nearest_poems = distances[1:11]

                # Store the similar poems in the dictionary
                similar_poems[pid] = []
                for order, (similar_pid, distance) in enumerate(
                    nearest_poems.items(), start=1
                ):
                    similar_poems[pid].append(
                        {
                            "poem_id": similar_pid,
                            "distance": distance,
                            "order": order,
                        }
                    )
            json_file_path = os.path.join(output_dir, "..", "similar_poems.json")
            with open(json_file_path, 'w') as json_file:
                json.dump(similar_poems, json_file, indent=4)

        elif os.path.exists("web/data/embeddings/embeddings3.csv"):
            from sklearn.metrics.pairwise import cosine_distances

            df = pd.read_csv("web/data/embeddings/embeddings3.csv")
            df["embedding"] = df["embedding"].apply(lambda x: np.array(eval(x)))

            os.makedirs(output_dir, exist_ok=True)
            grouped = df.groupby("cluster_id")
            for cluster_id, group in grouped:
                cluster_id = int(cluster_id)
                self.stdout.write(
                    self.style.SUCCESS(f"Processing cluster {cluster_id}.")
                )
                # Get the embeddings and pid values for the current cluster
                embeddings = np.vstack(group["embedding"].values)
                pids = group["pid"].values
                pids = [int(pid) for pid in pids]

                aggregated_embeddings = {}
                counts = {}

                for pid, embedding in zip(pids, embeddings):
                    if pid in aggregated_embeddings:
                        aggregated_embeddings[pid] += np.array(embedding)
                        counts[pid] += 1
                    else:
                        aggregated_embeddings[pid] = np.array(embedding)
                        counts[pid] = 1

                # Step 2: Compute the average embedding for each unique pid
                pids_dd = []
                embeddings_dd = []

                for pid, total_embedding in aggregated_embeddings.items():
                    average_embedding = total_embedding / counts[pid]
                    pids_dd.append(pid)
                    embeddings_dd.append(average_embedding.tolist())

                # Compute the cosine distance matrix
                distance_matrix = cosine_distances(embeddings_dd)

                # Create a DataFrame for the distance matrix with pid as index and columns
                distance_df = pd.DataFrame(distance_matrix, index=pids_dd, columns=pids_dd)
                distance_df = distance_df.round(3)

                # Save the distance matrix to a new CSV file
                output_file = os.path.join(
                    output_dir, f"cluster_{cluster_id}_distances.csv"
                )
                distance_df.to_csv(output_file)
            pass
        else:
            df = pd.read_csv("web/data/embeddings/embeddings2.csv")
            df["pid"] = None
            df["cluster_id"] = None
            for i in range(df.shape[0]):
                if i % 1000 == 0:
                    self.stdout.write(self.style.SUCCESS(f"Processing {i}th poem."))
                poem_id, cluster_id = find_poem_and_cluster_by_ccv_id(
                    df.loc[i, "poem_id"], df.loc[i, "book_id"]
                )
                df.loc[i, "pid"] = poem_id
                df.loc[i, "cluster_id"] = cluster_id
            df.to_csv("web/data/embeddings/embeddings3.csv")
