# Диаграмма базы данных TMDB-Net (SVG)

Ниже представлена диаграмма базы данных в формате Mermaid, который можно преобразовать в SVG с помощью различных онлайн-инструментов или плагинов для IDE.

```mermaid
erDiagram
    USER {
        int id PK
        string username
        string password
        string email
        string first_name
        string last_name
        bool is_staff
        bool is_active
        bool is_superuser
        datetime date_joined
        datetime last_login
    }
    
    MOVIE {
        int id PK
        int tmdb_id UK
        string title
        text overview
        string poster_path
        date release_date
        float vote_average
        int vote_count
        datetime created_at
        datetime updated_at
    }
    
    REVIEW {
        int id PK
        int user_id FK
        int movie_id FK
        text text
        int rating
        datetime created_at
        datetime updated_at
    }
    
    FAVORITE {
        int id PK
        int movie_id FK
        int user_id FK
    }
    
    USER ||--o{ REVIEW : оставляет
    MOVIE ||--o{ REVIEW : имеет
    USER }|--|| FAVORITE : имеет
    MOVIE }|--|| FAVORITE : в избранном
    FAVORITE }o--|| USER : принадлежит
    FAVORITE }o--|| MOVIE : относится к
```

## Как использовать эту диаграмму

1. **GitHub**: При загрузке этого файла в репозиторий GitHub, диаграмма будет автоматически отрендерена.

2. **Visual Studio Code**: 
   - Установите расширение "Mermaid Preview" или "Markdown Preview Mermaid Support"
   - Откройте этот файл и используйте предпросмотр Markdown

3. **Онлайн-редакторы**:
   - Вставьте код диаграммы на сайт [Mermaid Live Editor](https://mermaid.live/)
   - Экспортируйте результат в SVG или PNG

4. **Инструменты командной строки**:
   - Установите `mermaid-cli` через npm
   - Преобразуйте диаграмму в SVG с помощью команды `mmdc -i database_schema_svg.md -o database_schema.svg`

## Преимущества использования Mermaid

- Представление в виде кода (легко редактировать и поддерживать)
- Интеграция с системами контроля версий
- Возможность экспорта в различные форматы
- Поддержка в популярных средах разработки и документации 