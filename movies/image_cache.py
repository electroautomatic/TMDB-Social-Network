import os
import json
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)

def get_or_cache_poster(poster_path, size='w500', max_age_days=14):
    """
    Получает URL постера фильма, кэшируя его на сервере.
    
    Args:
        poster_path: Путь к постеру в TMDB (например, '/abc123.jpg')
        size: Размер изображения (w500, original и т.д.)
        max_age_days: Максимальный возраст кэша в днях
        
    Returns:
        URL к кэшированному изображению или None, если изображение недоступно
    """
    if not poster_path:
        return None
        
    # Удалить начальный слэш, если есть
    if poster_path.startswith('/'):
        poster_path = poster_path[1:]
        
    # Пути для файлов
    local_path = f"posters/{size}/{poster_path}"
    meta_path = f"posters/{size}/{poster_path}.meta"
    
    # Проверка на существование файла и его возраст
    if default_storage.exists(local_path):
        # Проверяем метаданные
        if default_storage.exists(meta_path):
            try:
                meta_content = default_storage.open(meta_path).read()
                metadata = json.loads(meta_content.decode('utf-8'))
                cached_date = datetime.fromisoformat(metadata['cached_date'])
                
                # Проверка возраста
                if datetime.now() - cached_date < timedelta(days=max_age_days):
                    # Обновляем дату последнего доступа
                    metadata['last_accessed'] = datetime.now().isoformat()
                    default_storage.delete(meta_path)
                    default_storage.save(meta_path, ContentFile(json.dumps(metadata).encode('utf-8')))
                    return default_storage.url(local_path)
                # Иначе продолжаем и перезагружаем
            except Exception as e:
                logger.warning(f"Error reading metadata for {poster_path}: {e}")
                
    # Загрузить изображение с TMDB
    tmdb_url = f"https://image.tmdb.org/t/p/{size}/{poster_path}"
    try:
        response = requests.get(tmdb_url, timeout=10)
        if response.status_code == 200:
            # Создаем директорию, если её нет
            path_dir = os.path.dirname(local_path)
            os.makedirs(os.path.join(settings.MEDIA_ROOT, path_dir), exist_ok=True)
            
            # Сохранить изображение
            default_storage.save(local_path, ContentFile(response.content))
            
            # Сохранить метаданные
            metadata = {
                'cached_date': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'original_url': tmdb_url,
                'size': size,
                'file_size': len(response.content)
            }
            default_storage.save(meta_path, ContentFile(json.dumps(metadata).encode('utf-8')))
            
            logger.info(f"Cached poster {poster_path} (size: {size})")
            return default_storage.url(local_path)
        else:
            logger.warning(f"Failed to download poster {poster_path}: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"Error downloading poster {poster_path}: {e}")
        
    return None

def check_cache_size(max_size_mb=500):
    """
    Проверяет размер кэша и очищает старые файлы, если превышен лимит
    
    Args:
        max_size_mb: Максимальный размер кэша в МБ
    
    Returns:
        tuple: (total_size_before, total_size_after, files_removed)
    """
    cache_dir = 'posters/'
    total_size = 0
    file_info = []
    
    # Проверяем существование директории
    if not default_storage.exists(cache_dir):
        return 0, 0, 0
    
    # Рекурсивно собираем информацию о файлах
    def collect_file_info(dir_path):
        nonlocal total_size
        try:
            dirs, files = default_storage.listdir(dir_path)
            for f in files:
                if not f.endswith('.meta'):
                    file_path = os.path.join(dir_path, f)
                    try:
                        size = default_storage.size(file_path)
                        
                        # Получаем время последнего доступа 
                        meta_path = file_path + '.meta'
                        accessed_time = datetime.now() - timedelta(days=365)  # По умолчанию очень старый
                        
                        if default_storage.exists(meta_path):
                            try:
                                meta_content = default_storage.open(meta_path).read()
                                metadata = json.loads(meta_content.decode('utf-8'))
                                # Используем last_accessed если есть, иначе cached_date
                                if 'last_accessed' in metadata:
                                    accessed_time = datetime.fromisoformat(metadata['last_accessed'])
                                else:
                                    accessed_time = datetime.fromisoformat(metadata['cached_date'])
                            except:
                                pass
                        
                        file_info.append({
                            'path': file_path,
                            'size': size,
                            'accessed': accessed_time,
                            'meta_path': meta_path
                        })
                        
                        total_size += size
                    except Exception as e:
                        logger.warning(f"Error processing file {file_path}: {e}")
            
            for d in dirs:
                new_dir = os.path.join(dir_path, d)
                collect_file_info(new_dir)
        except Exception as e:
            logger.error(f"Error accessing directory {dir_path}: {e}")
    
    collect_file_info(cache_dir)
    
    # Проверяем, не превышен ли лимит
    max_size_bytes = max_size_mb * 1024 * 1024
    total_size_before = total_size
    files_removed = 0
    
    if total_size > max_size_bytes:
        # Сортируем файлы по времени доступа (самые старые в начале)
        file_info.sort(key=lambda x: x['accessed'])
        
        # Удаляем старые файлы, пока не освободится достаточно места
        size_to_free = total_size - max_size_bytes
        freed = 0
        
        for file_data in file_info:
            # Удаляем файл и его метаданные
            try:
                default_storage.delete(file_data['path'])
                if default_storage.exists(file_data['meta_path']):
                    default_storage.delete(file_data['meta_path'])
                
                freed += file_data['size']
                files_removed += 1
                
                if freed >= size_to_free:
                    break
            except Exception as e:
                logger.error(f"Error removing file {file_data['path']}: {e}")
        
        logger.info(f"Cache cleanup: removed {freed / (1024*1024):.2f} MB ({files_removed} files)")
    
    return total_size_before, total_size_before - freed if 'freed' in locals() else total_size, files_removed 