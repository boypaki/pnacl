import os
from flask import Blueprint, render_template, send_file, request, redirect, url_for, current_app, abort, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models.downloads import Download, DownloadLog
from sqlalchemy import desc

downloads_blueprint = Blueprint('downloads', __name__)

@downloads_blueprint.route('/')
def list_downloads():
    # Obter downloads organizados por plataforma e versão
    windows_versions = Download.query.filter_by(platform='windows').order_by(desc(Download.upload_date)).all()
    mac_versions = Download.query.filter_by(platform='mac').order_by(desc(Download.upload_date)).all()
    linux_versions = Download.query.filter_by(platform='linux').order_by(desc(Download.upload_date)).all()
    
    return render_template('downloads/list.html', 
                          windows=windows_versions,
                          mac=mac_versions,
                          linux=linux_versions)

@downloads_blueprint.route('/download/<int:download_id>')
def download_file(download_id):
    # Obter arquivo
    download = Download.query.get_or_404(download_id)
    
    # Verificar se o arquivo existe
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], download.filename)
    
    if not os.path.exists(file_path):
        abort(404)
    
    # Registrar download
    download.increment_download()
    
    # Registrar log de download
    log = DownloadLog(
        download_id=download.id,
        user_id=current_user.id if current_user.is_authenticated else None,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.add(log)
    db.session.commit()
    
    # Enviar arquivo
    return send_file(file_path, as_attachment=True)

@downloads_blueprint.route('/admin/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    # Verificar permissão de admin
    if not current_user.is_admin:
        abort(403)
    
    if request.method == 'POST':
        # Verificar se há arquivo na requisição
        if 'file' not in request.files:
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        
        # Verificar se o arquivo tem nome
        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.url)
            
        # Verificar extensão
        allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
        if not file.filename.split('.')[-1].lower() in allowed_extensions:
            flash(f'Extensão não permitida. Use: {", ".join(allowed_extensions)}', 'danger')
            return redirect(request.url)
            
        # Salvar arquivo
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Obter tamanho do arquivo
        size_bytes = os.path.getsize(file_path)
        
        # Obter informações do formulário
        version = request.form.get('version')
        platform = request.form.get('platform')
        description = request.form.get('description', '')
        is_latest = 'is_latest' in request.form
        
        # Se marcado como latest, desmarcar outros da mesma plataforma
        if is_latest:
            Download.query.filter_by(platform=platform, is_latest=True).update({'is_latest': False})
        
        # Criar registro no banco
        download = Download(
            filename=filename,
            version=version,
            platform=platform,
            size_bytes=size_bytes,
            is_latest=is_latest,
            description=description
        )
        
        db.session.add(download)
        db.session.commit()
        
        flash('Arquivo enviado com sucesso', 'success')
        return redirect(url_for('downloads.list_downloads'))
    
    return render_template('downloads/upload.html')
