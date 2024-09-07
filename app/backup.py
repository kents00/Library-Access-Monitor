import shutil
import os
from datetime import datetime

db_path = 'library.db'
backup_dir = 'backup/'

if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

backup_file = os.path.join(backup_dir, f'backup_{
                           datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
shutil.copy2(db_path, backup_file)
print(f'Backup created at {backup_file}')
