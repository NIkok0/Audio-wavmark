from watermark import app, db
import click
import os
from watermark.models import User, Group, File
from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError

@app.cli.command()  # 注册为命令，可以传入 name 参数来自定义命令
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项
def initdb(drop):
    """Initialize the database and create default super admin."""
    if drop:  # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    
    # 添加缺失的列（如果数据库表已存在但结构不完整）
    _add_missing_columns()
    
    # 创建默认超级管理员（若不存在）
    from werkzeug.security import generate_password_hash

    default_username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
    default_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin')
    default_email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@example.com')

    try:
        existing = User.query.filter_by(username=default_username).first()
    except OperationalError:
        # 可能需要再次添加缺失的列
        _add_missing_columns()
        db.session.rollback()
        existing = User.query.filter_by(username=default_username).first()
    
    if not existing:
        user = User(
            username=default_username,
            email=default_email,
            password=generate_password_hash(default_password),
            is_admin=True,
            role='super_admin'
        )
        db.session.add(user)
        db.session.commit()
        click.echo(f'Created default super admin user: {default_username} ({default_email})')
    else:
        click.echo('Default super admin already exists.')

    click.echo('Initialized database.')

def _add_missing_columns():
    """Add missing columns to existing tables"""
    # Model schema definitions
    models_schema = {
        'users': {
            'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
            'updated_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
            'is_active': 'BOOLEAN DEFAULT TRUE',
            'is_embed': 'BOOLEAN DEFAULT TRUE',
            'is_extract': 'BOOLEAN DEFAULT TRUE',
            'role': "VARCHAR(20) DEFAULT 'member'",
            'retention_days': 'INT NULL',
        }
    }
    
    inspector = inspect(db.engine)
    
    for table_name, columns_schema in models_schema.items():
        try:
            # 获取数据库中实际存在的列
            db_columns = {col['name'] for col in inspector.get_columns(table_name)}
        except Exception:
            # 表可能不存在，跳过
            continue
        
        # 找出缺失的列
        missing_columns = set(columns_schema.keys()) - db_columns
        
        if missing_columns:
            for col_name in missing_columns:
                col_type = columns_schema[col_name]
                try:
                    alter_sql = f"ALTER TABLE {table_name} ADD COLUMN `{col_name}` {col_type}"
                    with db.engine.begin() as conn:
                        conn.execute(text(alter_sql))
                except Exception as e:
                    pass  # 列可能已经存在，忽略错误

@app.cli.command()
@click.option('--username', prompt=True, help='The username of the admin')
@click.option('--email', prompt=True, help='The email of the admin')
@click.option('--password', prompt=True, hide_input=True, help='The password of the admin')
def create_admin(username, email, password):
    """Create an admin user."""
    from werkzeug.security import generate_password_hash
    user = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        is_admin=True
    )
    db.session.add(user)
    db.session.commit()
    click.echo(f'Created admin user: {username} ({email})')

@app.cli.command()
def check_missing_columns():
    """Check and add missing database columns."""
    from sqlalchemy.exc import OperationalError
    
    models_to_check = {
        'users': User,
        'groups': Group,
        'files': File
    }
    
    inspector = inspect(db.engine)
    
    for table_name, model in models_to_check.items():
        click.echo(f'\nChecking table: {table_name}')
        
        # 获取数据库中实际存在的列
        try:
            db_columns = {col['name'] for col in inspector.get_columns(table_name)}
        except Exception as e:
            click.echo(f'  ⚠️  Table {table_name} does not exist yet')
            continue
        
        # 获取模型定义的列
        model_columns = {col.name for col in model.__table__.columns}
        
        # 找出缺失的列
        missing_columns = model_columns - db_columns
        
        if missing_columns:
            click.echo(f'  ❌ Missing columns: {missing_columns}')
            
            # 添加缺失的列
            for col_name in missing_columns:
                col = model.__table__.columns[col_name]
                # 构造 ALTER TABLE 语句
                col_type = str(col.type)
                default_val = 'NULL'
                
                if col.default is not None:
                    if callable(col.default.arg):
                        default_val = "''"
                    elif isinstance(col.default.arg, str):
                        default_val = f"'{col.default.arg}'"
                    elif col.default.arg is True:
                        default_val = 'TRUE'
                    elif col.default.arg is False:
                        default_val = 'FALSE'
                    else:
                        default_val = str(col.default.arg)
                elif not col.nullable:
                    if col_type.upper().startswith('VARCHAR'):
                        default_val = "''"
                    elif col_type.upper().startswith('INT'):
                        default_val = '0'
                    elif col_type.upper().startswith('BOOL'):
                        default_val = 'FALSE'
                    elif col_type.upper().startswith('DATETIME'):
                        default_val = 'CURRENT_TIMESTAMP'
                    else:
                        default_val = 'NULL'
                
                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN `{col_name}` {col_type} DEFAULT {default_val}"
                try:
                    with db.engine.begin() as conn:
                        conn.execute(text(alter_sql))
                    click.echo(f'  ✓ Added column: {col_name}')
                except Exception as add_err:
                    click.echo(f'  ⚠️  Failed to add column {col_name}: {add_err}')
        else:
            click.echo(f'  ✓ All columns present')

    click.echo(f'Created admin user: {username} ({email})')