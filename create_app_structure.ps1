# create_app_structure.ps1
# Створює проектну структуру у поточній директорії

$root = (Get-Location).Path

$folders = @(
    "app",
    "app\core",
    "app\db",
    "app\models",
    "app\schemas",
    "app\crud",
    "app\api",
    "app\routers",
    "app\web",
    "app\views",
    "app\templates",
    "app\static",
    "app\static\css",
    "app\static\js"
)

$files = @(
    "app\__init__.py",
    "app\main.py",

    "app\core\__init__.py",
    "app\core\config.py",

    "app\db\__init__.py",
    "app\db\session.py",

    "app\models\__init__.py",
    "app\models\base.py",
    "app\models\supplier.py",

    "app\schemas\__init__.py",
    "app\schemas\supplier.py",

    "app\crud\__init__.py",
    "app\crud\supplier.py",

    "app\api\__init__.py",
    "app\api\deps.py",
    "app\api\routes.py",

    "app\routers\__init__.py",
    "app\routers\suppliers.py",

    "app\web\__init__.py",
    "app\web\router.py",

    "app\views\__init__.py",
    "app\views\suppliers.py",

    "app\templates\layout.html",
    "app\templates\suppliers.html",
    "app\templates\supplier_form.html",

    "requirements.txt",
    ".env.example",
    "db_reset.py",
    "seed_minimal.py"
)

# Створити папки
foreach ($f in $folders) {
    $p = Join-Path $root $f
    if (-not (Test-Path $p)) {
        New-Item -ItemType Directory -Path $p | Out-Null
        Write-Host "Created folder: $p"
    } else {
        Write-Host "Folder exists: $p"
    }
}

# Створити файли
foreach ($f in $files) {
    $p = Join-Path $root $f
    if (-not (Test-Path $p)) {
        # Гарантуємо, що батьківська папка існує
        $parent = Split-Path $p -Parent
        if (-not (Test-Path $parent)) {
            New-Item -ItemType Directory -Path $parent | Out-Null
        }
        New-Item -ItemType File -Path $p | Out-Null
        Write-Host "Created file: $p"
    } else {
        Write-Host "File exists: $p"
    }
}

Write-Host "`nDone."
