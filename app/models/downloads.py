from datetime import datetime
from app import db

class Download(db.Model):
    __tablename__ = 'downloads'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    platform = db.Column(db.String(20), nullable=False)  # windows, mac, linux
    size_bytes = db.Column(db.Integer, nullable=False)
    is_latest = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text, nullable=True)
    download_count = db.Column(db.Integer, default=0)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    download_logs = db.relationship('DownloadLog', backref='download', lazy=True)
    
    def increment_download(self):
        """Incrementa o contador de downloads"""
        self.download_count += 1
        db.session.commit()
    
    def __repr__(self):
        return f'<Download {self.filename} {self.version}>'

class DownloadLog(db.Model):
    __tablename__ = 'download_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    download_id = db.Column(db.Integer, db.ForeignKey('downloads.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DownloadLog {self.download_id} by User {self.user_id}>'
