from django.core.management.base import BaseCommand
from web.models import Book, Poem
from web.utils import remove_html_tags
import pandas as pd
import Levenshtein
import re

def get_text(old_poem_id):
    id = str(old_poem_id)
    while len(id) < 6:
        id = '0' + id
    with open(f"./web/data/poem_files/{id}.txt", 'r') as file:
        text = file.read()
    return text

def clean_string(input_string):
    cleaned_string = re.sub(r'\s+', ' ', input_string)
    cleaned_string = cleaned_string.lower().strip()
    return cleaned_string

manual_links = { # id in ccv : id in cek
    # book 67
    2672 : 6700107,
    2694 : 6700129,
    # book 193
    9561: 19300003,
    9566: 19300008,
    9567: 19300009,
    9594: 19300036,
    9598: 19300040,
    9659: 19300101,
    9670: 19300112,
    9715: 19300157,
    # book 212
    10503: 21200002,
    10572: 21200071,
    10581: 21200080,
    10598: 21200097,
    # book 674
    30375: 67400069,
    # book 680
    30677: 68000080,
    30684: 68000087,
    # book 692
    30910: 69200008,
    30911: 69200009,
    30913: 69200011,
    30914: 69200012,
    30915: 69200013,
    30916: 69200014,
    30917: 69200015,
    30918: 69200016,
    30921: 69200019,
    30922: 69200020,
    30925: 69200023,
    30926: 69200024,
    30927: 69200025,
    30928: 69200026,
    30929: 69200027,
    30931: 69200029,
    30932: 69200030,
    30934: 69200032,
    30935: 69200033,
    30936: 69200034,
    30937: 69200035,
    30938: 69200036,
    30939: 69200037,
    30941: 69200039,
    30948: 69200046,
    30951: 69200049,
    30953: 69200051,
    30956: 69200054,
    30959: 69200057,
    30961: 69200059,
    31000: 69200078,
    31001: 69200079,
    31003: 69200081,
    31132: 69200213,
    31134: 69200215,
    31136: 69200217,
    31138: 69200219,
    31139: 69200220,
    31142: 69200223,
    31146: 69200227,
    31147: 69200228,
    31148: 69200229,
    31149: 69200032,
    31150: 69200231,
    31151: 69200030,
    31152: 69200233,
    31153: 69200234,
    31154: 69200235,
    31155: 69200236,
    31156: 69200237,
    31157: 69200238,
    31158: 69200239,
    31159: 69200240,
    31160: 69200241,
    31161: 69200242,
    31163: 69200244,
    31164: 69200245,
    31165: 69200246,
    31166: 69200247,
    31169: 69200250,
    # book 878
    38993: 87800010,
    39109: 87800100,
    39110: 87800101,

}

# duplicities in cek
duplicities = [
    # book 67
    [6700107, 6700129],
    # book 193
    [19300003, 19300101],
    [19300009, 19300141],
    [19300008, 19300040],
    [19300112, 19300213],
    [19300036, 19300157],
    # book 212
    [21200002, 21200097],
    [21200071, 21200080],
    # book 674
    [67400069, 67400083], # první je strofa té druhé
    # book 680
    [68000080, 68000087], 
    # book 692
    [69200008, 69200236],
    [69200009, 69200237],
    [69200011, 69200239],
    [69200012, 69200240],
    [69200013, 69200241],
    [69200014, 69200079],
    [69200015, 69200242],
    [69200016, 69200238],
    [69200019, 69200244],
    [69200020, 69200245],
    [69200023, 69200246],
    [69200024, 69200247],
    [69200025, 69200229],
    [69200026, 69200227],
    [69200027, 69200228],
    [69200029, 69200231],
    [69200030, 69200232],
    [69200032, 69200230],
    [69200033, 69200217],
    [69200034, 69200219],
    [69200035, 69200220],
    [69200036, 69200223],
    [69200037, 69200078],
    [69200039, 69200081],
    [69200046, 69200235],
    [69200049, 69200234],
    [69200051, 69200233],
    [69200054, 69200250],
    [69200057, 69200213],
    [69200059, 69200215],
    [69200037, 69200078],
    [69200014, 69200079],
    [69200039, 69200081],
    [69200057, 69200213],
    [69200059, 69200215],
    [69200033, 69200217],
    [69200034, 69200219],
    [69200035, 69200220],
    [69200036, 69200223],
    [69200026, 69200227],
    [69200027, 69200228],
    [69200025, 69200229],
    [69200032, 69200230],
    [69200029, 69200231],
    [69200030, 69200232],
    [69200051, 69200233],
    [69200049, 69200234],
    [69200046, 69200235],
    [69200008, 69200236],
    [69200009, 69200237],
    [69200016, 69200238],
    [69200011, 69200239],
    [69200012, 69200240],
    [69200013, 69200241],
    [69200015, 69200242],
    [69200019, 69200244],
    [69200020, 69200245],
    [69200023, 69200246],
    [69200024, 69200247],
    [69200054, 69200250],
    # book 878
    [87800010, 87800101],
    [87800025, 87800100],
]

class Command(BaseCommand):
    help = ''

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str)

    def handle(self, *args, **options):
        csv_file_path = options['csv_file_path']
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            df = pd.read_csv(csvfile)
        if True:
            df_output = pd.read_csv('./web/data/web_ccv_template.csv')
            for book in Book.objects.filter(id__range=(0,1700)).all().order_by('id'):
                print(f"================= Book id: {book.id} ================")
                poems = book.poems.all().order_by('order_in_book')
                df_poems = df[(df['book_id']==book.id) & ((df.part_order <= 1.0) | (df.part_order.isnull()))]
                # print(df_poems)
                ccv_assignments = {} # ccv_id => [cek_id]
                for i in range(len(df_poems)):
                    ccv_assignments[df_poems.iloc[i]['id']] = []
                cek_assignments = {} # cek_id => [ccv_id]
                for p in poems:
                    cek_assignments[p.id] = []
                for p in poems:
                    cek_text_complete = clean_string(remove_html_tags(p.text))
                    for i in range(len(df_poems)):
                        ccv_id = df_poems.iloc[i]['id']
                        if int(ccv_id) in manual_links and manual_links[ccv_id] == p.id:
                            ccv_assignments[ccv_id].append(p.id)
                            cek_assignments[p.id].append(ccv_id)
                            continue
                        elif int(ccv_id) in manual_links:
                            continue
                        ccv_text = clean_string(get_text(ccv_id))
                        if len(ccv_text) >= len(cek_text_complete)*1.5:
                            continue
                        cek_text = cek_text_complete[:len(ccv_text)*2]
                        diff = max(len(ccv_text), len(cek_text)) - min(len(ccv_text), len(cek_text))
                        ld = Levenshtein.distance(cek_text, ccv_text)
                        ldr = (ld - diff)/(min(len(ccv_text), len(cek_text)))
                        if ldr <= 0.08:
                            ccv_assignments[ccv_id].append(p.id)
                            cek_assignments[p.id].append(ccv_id)
                        else:
                            # print(f"cek {p.id} vs ccv {ccv_id}: ld = {ld}, diff = {diff}, ldr = {ldr}")
                            pass
                all_good = True
                for ccv_id, ids in ccv_assignments.items():
                    data = {
                        'id' : '',
                        'ccv_id' : '',
                        'ccv_title' : '',
                        'ccv_author' : '',
                        'ccv_year' : '',
                        'ccv_poem_id' : '',
                        'ccv_book_id' : '',
                        'ccv_part_of' : '',
                        'ccv_part_order' : '',
                        'ccv_next_issue_of' : '',
                        'cek_part_of' : '',
                        'cek_next_issue_of' : ''
                    }
                    if len(ids) < 1:
                        all_good = False
                        print(f"{ccv_id}: not found") 
                    elif len(ids) > 1:
                        all_good = False
                        print(f"{ccv_id}: {ids} fits found")
                        self.stdout.write(self.style.ERROR(f"{ccv_id}: {ids} fits found")) 
                    else:
                        cek_id = ids[0]
                        data['id'] = cek_id
                        data['ccv_id'] = int(ccv_id)
                        row = df_poems[df_poems.id == ccv_id].iloc[0,:]
                        data['ccv_title'] = row['title']
                        data['ccv_author'] = row['author']
                        data['ccv_year'] = row['year']
                        data['ccv_poem_id'] = row['poem_id']
                        data['ccv_book_id'] = row['book_id']
                        data['ccv_part_of'] = int(row['part_of']) if not pd.isna(row['part_of']) else ''
                        data['ccv_part_order'] = int(row['part_order']) if not pd.isna(row['part_order']) else ''
                        data['ccv_next_issue_of'] = int(row['next_issue_of']) if not pd.isna(row['next_issue_of']) else ''
                        data['cek_part_of'] = ''
                        data['cek_next_issue_of'] = ''
                        df_output = pd.concat([df_output, pd.DataFrame([data])], ignore_index=True)
                if all_good:
                    # print(f"Book {book.id}: all OK!")
                    pass
            df_output.to_csv('./web/data/web_ccv.csv')
        else:
            df_output = pd.read_csv('./web/data/web_ccv.csv', index_col=0)        
        
        # parts of poems
        df_output_parts = pd.DataFrame(columns=df_output.columns)
        df_with_parts = df_output[df_output['ccv_part_of'] == df_output['ccv_id']]
        for j in range(len(df_with_parts)):
            cek_id = df_with_parts.iloc[j]['id']
            ccv_id = df_with_parts.iloc[j]['ccv_id']
            df_parts = df[(df.part_of == ccv_id) & (df.id != ccv_id)]
            for i in range(len(df_parts)):
                row = df_parts.iloc[i,:]
                data = {}
                data['id'] = int(cek_id)
                data['ccv_id'] = row['id']
                data['ccv_title'] = row['title']
                data['ccv_author'] = row['author']
                data['ccv_year'] = row['year']
                data['ccv_poem_id'] = row['poem_id']
                data['ccv_book_id'] = row['book_id']
                data['ccv_part_of'] = int(row['part_of']) if not pd.isna(row['part_of']) else ''
                data['ccv_part_order'] = int(row['part_order']) if not pd.isna(row['part_order']) else ''
                data['ccv_next_issue_of'] = int(row['next_issue_of']) if not pd.isna(row['next_issue_of']) else ''
                data['cek_part_of'] = ''
                data['cek_next_issue_of'] = ''
                df_output_parts = pd.concat([df_output_parts, pd.DataFrame([data])], ignore_index=True)
        df_output = pd.concat([df_output, df_output_parts], ignore_index=True)

        # ccv_ids to cek_ids
        ccv_to_cek = {}
        for i in range(df_output.shape[0]):
            ccv_to_cek[df_output.iloc[i]['ccv_id']] = df_output.iloc[i]['id']

        df_output.fillna('', inplace=True)
        for i in df_output.index:
            if df_output.loc[i,'ccv_part_of'] != '':
                if df_output.loc[i,'ccv_part_of'] in ccv_to_cek:
                    df_output.loc[i,'cek_part_of'] = ccv_to_cek[df_output.loc[i,'ccv_part_of']]
                else:
                     self.stdout.write(self.style.ERROR(f"Part of ccv_id {df_output.loc[i,'ccv_part_of']} not resolved"))
            if df_output.loc[i,'ccv_next_issue_of'] != '':
                if df_output.loc[i,'ccv_next_issue_of'] in ccv_to_cek:
                    df_output.loc[i,'cek_next_issue_of'] = ccv_to_cek[df_output.loc[i,'ccv_next_issue_of']]
                else:
                     self.stdout.write(self.style.ERROR(f"Next issue of ccv_id {df_output.loc[i,'ccv_next_issue_of']} not resolved"))
        df_output.to_csv('./web/data/web_ccv.csv')