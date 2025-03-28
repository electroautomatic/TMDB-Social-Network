from django.core.management.base import BaseCommand
from django.conf import settings
from datetime import datetime, timedelta
import json
import os
from movies.image_cache import check_cache_size

class Command(BaseCommand):
    help = 'Clean old cached movie posters'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=14, 
                          help='Remove images older than this many days')
        parser.add_argument('--max-size', type=int, default=500,
                          help='Maximum cache size in MB')
        parser.add_argument('--dry-run', action='store_true',
                          help='Show what would be done without actually removing files')

    def handle(self, *args, **options):
        days = options['days']
        max_size_mb = options['max_size']
        dry_run = options['dry_run']
        
        self.stdout.write(f"Cleaning image cache older than {days} days")
        self.stdout.write(f"Maximum cache size: {max_size_mb} MB")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no files will be deleted"))
            
        # Сначала проверяем по возрасту
        from django.core.files.storage import default_storage
        
        posters_dir = 'posters/'
        if not default_storage.exists(posters_dir):
            self.stdout.write(self.style.WARNING("Posters directory does not exist"))
            return
            
        cutoff_date = datetime.now() - timedelta(days=days)
        self.stdout.write(f"Cutoff date: {cutoff_date.isoformat()}")
        
        # Собираем мета-файлы для проверки
        paths = []
        
        def collect_meta_paths(dir_path):
            try:
                dirs, files = default_storage.listdir(dir_path)
                for f in files:
                    if f.endswith('.meta'):
                        paths.append(os.path.join(dir_path, f))
                for d in dirs:
                    collect_meta_paths(os.path.join(dir_path, d))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing directory {dir_path}: {e}"))
        
        collect_meta_paths(posters_dir)
        self.stdout.write(f"Found {len(paths)} cached images")
        
        # Проверяем метаданные каждого файла
        removed_count = 0
        removed_size = 0
        
        for meta_path in paths:
            try:
                meta_content = default_storage.open(meta_path).read()
                metadata = json.loads(meta_content.decode('utf-8'))
                cached_date = datetime.fromisoformat(metadata['cached_date'])
                
                # Если файл старше cutoff_date, удаляем его
                if cached_date < cutoff_date:
                    # Путь к самому изображению (без .meta)
                    image_path = meta_path[:-5]  # удаляем '.meta'
                    
                    if default_storage.exists(image_path):
                        size = default_storage.size(image_path)
                        removed_size += size
                        
                        if not dry_run:
                            # Удаляем изображение
                            default_storage.delete(image_path)
                            # Удаляем метаданные
                            default_storage.delete(meta_path)
                            
                        removed_count += 1
                        self.stdout.write(f"Removing {image_path} (age: {(datetime.now() - cached_date).days} days)")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {meta_path}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(
            f"Age-based cleanup: {'Would remove' if dry_run else 'Removed'} {removed_count} "
            f"old cached images ({removed_size / (1024*1024):.2f} MB)"
        ))
        
        # Затем проверяем по размеру
        if not dry_run:
            before_size, after_size, files_removed = check_cache_size(max_size_mb)
            
            self.stdout.write(self.style.SUCCESS(
                f"Size-based cleanup: Cache size {before_size / (1024*1024):.2f} MB -> "
                f"{after_size / (1024*1024):.2f} MB, removed {files_removed} files"
            ))
        else:
            # В режиме dry run просто показываем текущий размер
            from movies.image_cache import check_cache_size
            total_size = 0
            
            def get_dir_size(dir_path):
                nonlocal total_size
                try:
                    dirs, files = default_storage.listdir(dir_path)
                    for f in files:
                        if not f.endswith('.meta'):
                            file_path = os.path.join(dir_path, f)
                            try:
                                total_size += default_storage.size(file_path)
                            except Exception:
                                pass
                    for d in dirs:
                        get_dir_size(os.path.join(dir_path, d))
                except Exception:
                    pass
            
            get_dir_size(posters_dir)
            
            self.stdout.write(self.style.SUCCESS(
                f"Current cache size: {total_size / (1024*1024):.2f} MB"
            ))
            
            if total_size > max_size_mb * 1024 * 1024:
                self.stdout.write(self.style.WARNING(
                    f"Cache size exceeds maximum ({max_size_mb} MB), would trigger cleanup"
                ))
        
        self.stdout.write(self.style.SUCCESS("Cache cleanup completed")) 