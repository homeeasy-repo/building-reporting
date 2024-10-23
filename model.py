from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Company(db.Model):
    __tablename__ = 'company'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)

    buildings = db.relationship("Building", back_populates="company")

    def __repr__(self):
        return f"<Company(id={self.id}, name={self.name})>"

class Client(db.Model):
    __tablename__ = 'client'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created = db.Column(db.DateTime, server_default=db.func.now(), nullable=True)
    salary = db.Column(db.String(50), nullable=True)
    addresses = db.Column(db.Text, nullable=True)
    fullname = db.Column(db.String(100), nullable=True)
    assigned_employee_name = db.Column(db.String(100), nullable=True)

    stage_progressions = db.relationship("ClientStageProgression", back_populates="client")
    property_discoveries = db.relationship("ClientPropDiscovery", back_populates="client")
    text_messages = db.relationship("TextMessage", back_populates="client")

    def __repr__(self):
        return f"<Client(id={self.id}, fullname={self.fullname}, addresses={self.addresses})>"

class ClientStageProgression(db.Model):
    __tablename__ = 'client_stage_progression'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    stage_name = db.Column(db.String(100), nullable=True)
    current_stage = db.Column(db.Integer, nullable=False)
    created_on = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    client = db.relationship("Client", back_populates="stage_progressions")

    def __repr__(self):
        return f"<ClientStageProgression(id={self.id}, client_id={self.client_id}, stage_name={self.stage_name}, current_stage={self.current_stage})>"

class TextMessage(db.Model):
    __tablename__ = 'textmessage'

    id = db.Column(db.Integer, primary_key=True)
    from_number = db.Column(db.String(20), nullable=True)
    to_number = db.Column(db.String(20), nullable=True)
    message = db.Column(db.Text, nullable=True)
    read = db.Column(db.Boolean, nullable=True)
    created_by = db.Column(db.Integer, nullable=True)
    updated_by = db.Column(db.Integer, nullable=True)
    created = db.Column(db.DateTime, nullable=True)
    updated = db.Column(db.DateTime, nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    sent = db.Column(db.DateTime, nullable=True)
    is_incoming = db.Column(db.Boolean, nullable=True)
    shared_inbox_id = db.Column(db.Integer, nullable=True)
    archived = db.Column(db.Boolean, nullable=True)
    group_text_id = db.Column(db.Integer, nullable=True)
    participants = db.Column(db.JSON, nullable=True)
    may_processed = db.Column(db.Boolean, nullable=True)

    client = db.relationship("Client", back_populates="text_messages")

    def __repr__(self):
        return f"<TextMessage(id={self.id}, from_number={self.from_number}, to_number={self.to_number}, status={self.status})>"

class ClientPropDiscovery(db.Model):
    __tablename__ = 'client_prop_discovery'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    bld_name = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    alternate_phone = db.Column(db.String(20), nullable=True)
    sponsor = db.Column(db.String(150), nullable=True)
    property_specials = db.Column(db.Text, nullable=True)
    verified_listing = db.Column(db.Boolean, default=False)
    called = db.Column(db.Boolean, default=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    b_id = db.Column(db.Integer, db.ForeignKey('building.id'), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    zip = db.Column(db.String(20), nullable=True)
    called_at = db.Column(db.DateTime, nullable=True)
    property_link = db.Column(db.String(255), nullable=True)
    ans_by_human = db.Column(db.Boolean, default=False)

    client = db.relationship("Client", back_populates="property_discoveries")

    def __repr__(self):
        return f"<ClientPropDiscovery(id={self.id}, client_id={self.client_id}, bld_name={self.bld_name})>"

class Building(db.Model):
    __tablename__ = 'building'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    zip = db.Column(db.String(20), nullable=True)
    building_type = db.Column(db.String(50), nullable=True)
    cooperate = db.Column(db.Boolean, default=True, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    scrape_city = db.Column(db.String(100), nullable=True)
    address_full = db.Column(db.Text, nullable=True)
    media_count = db.Column(db.Integer, default=0, nullable=True)
    migrated = db.Column(db.DateTime, nullable=True)
    showing_type = db.Column(db.String(50), nullable=True)
    cooperate_status_unsure = db.Column(db.Boolean, default=False, nullable=True)
    cooperate_status_sure = db.Column(db.Boolean, default=False, nullable=True)
    cooperate_status_false = db.Column(db.Boolean, default=False, nullable=True)
    amenities = db.Column(db.JSON, nullable=True)

    company = db.relationship("Company", back_populates="buildings")

    def __repr__(self):
        return f"<Building(id={self.id}, name={self.name}, address={self.address}, city={self.city}, state={self.state})>"


